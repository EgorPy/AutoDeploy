from core.method_generator import AutoDB, cm
from backend.schema import Services

import subprocess
import platform
import signal
import json
import time
import os

db = AutoDB(cm)
IS_WINDOWS = platform.system() == "Windows"
DEBUG = False
KEEP_CONSOLE = True


def _get_new_pids(pids_before, main_pid, workdir):
    try:
        import psutil

        pids_after = set(p.pid for p in psutil.process_iter())
        new_pids = pids_after - pids_before - {main_pid}

        result = []
        workdir_lower = workdir.lower()

        for pid in new_pids:
            try:
                p = psutil.Process(pid)
                exe = p.exe().lower()
                cwd = p.cwd().lower()
                cmdline = " ".join(p.cmdline()).lower()

                is_related = (
                        cwd.startswith(workdir_lower) or
                        exe.startswith(workdir_lower) or
                        workdir_lower in cmdline  # скрипт запущен из workdir
                )

                if is_related:
                    result.append(pid)
                    print(f"[INFO] Detected child PID {pid}: {exe} | cwd={cwd}")
                else:
                    if DEBUG:
                        print(f"[DEBUG] Skipping PID {pid}: {exe} | cwd={cwd}")

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return result

    except Exception as e:
        print(f"[WARN] Could not detect child PIDs: {e}")
        return []


def _get_all_pids():
    try:
        import psutil
        return set(p.pid for p in psutil.process_iter())
    except Exception:
        return set()


def _is_python_cmd(cmd: str) -> bool:
    name = os.path.basename(cmd).lower()
    return name.startswith("python")


def _build_env(venv_path, workdir):
    env = os.environ.copy()

    if venv_path:
        if os.name == "nt":  # Windows
            bin_dir = os.path.join(venv_path, "Scripts")
        else:
            bin_dir = os.path.join(venv_path, "bin")

        env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
        env["VIRTUAL_ENV"] = venv_path
        env.pop("PYTHONHOME", None)

    env["PYTHONPATH"] = workdir

    return env


def _resolve_venv(service):
    workdir = service["workdir"]

    custom = service.get("venv_path")
    if custom:
        # Если путь уже указывает прямо на venv папку — используем как есть
        if os.path.exists(os.path.join(custom, "Scripts", "python.exe")) or \
                os.path.exists(os.path.join(custom, "bin", "python")):
            return custom

        # Иначе пробуем добавить .venv и venv
        for name in (".venv", "venv"):
            candidate = os.path.join(custom, name)
            if os.path.exists(candidate):
                return candidate

    # Локальный .venv или venv внутри workdir
    for name in (".venv", "venv"):
        local = os.path.join(workdir, name)
        if os.path.exists(local):
            return local

    return None


def start(service):
    service_id = service["id"]
    cmd = service["run_command"]
    workdir = service["workdir"]

    if not cmd:
        print(f"[WARN] Service {service_id} has no run_command")
        return

    venv_path = _resolve_venv(service)

    venv_python = None
    if venv_path:
        py_path = os.path.join(venv_path, "Scripts", "python.exe") if os.name == "nt" \
            else os.path.join(venv_path, "bin", "python")
        if os.path.exists(py_path):
            venv_python = py_path
        else:
            print(f"[WARN] venv found at {venv_path} but python not found")

    parts = cmd.split()

    if venv_python and _is_python_cmd(parts[0]):
        parts[0] = venv_python

    env = _build_env(venv_path, workdir)

    kwargs = dict(cwd=workdir, shell=False, env=env)

    if IS_WINDOWS:
        if KEEP_CONSOLE:
            parts = ["cmd", "/k"] + parts
        kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
    else:
        kwargs["start_new_session"] = True

    if DEBUG:
        print(f"[DEBUG] parts: {parts}")
        print(f"[DEBUG] cwd: {workdir}")
        print(f"[DEBUG] venv_python: {venv_python}")
        print(f"[DEBUG] venv_path: {venv_path}")

    try:
        pids_before = _get_all_pids()
        process = subprocess.Popen(parts, **kwargs)

        time.sleep(5)

        new_pids = _get_new_pids(pids_before, process.pid, workdir)

        print(f"[INFO] Service {service_id} started with PID {process.pid}")
        print(f"[INFO] Detected child PIDs: {new_pids}")

        db.update(Services, {
            "pid": process.pid,
            "child_pids": json.dumps(new_pids)
        }, {"id": service_id})

    except Exception as e:
        print(f"[ERROR] Failed to start service {service_id}: {e}")


def _kill_tree_windows(pid):
    try:
        import psutil
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        # Сначала убиваем детей
        for child in children:
            try:
                subprocess.call(f"taskkill /PID {child.pid} /F", shell=True)
            except Exception:
                pass
        # Потом родителя
        subprocess.call(f"taskkill /PID {pid} /F", shell=True)
    except Exception as e:
        # psutil недоступен или процесс уже мёртв — fallback
        subprocess.call(f"taskkill /PID {pid} /T /F", shell=True)


def _kill_tree_linux(pid):
    try:
        import psutil
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            try:
                os.kill(child.pid, signal.SIGTERM)
            except Exception:
                pass
    except Exception:
        pass

    # Убиваем всю process group
    try:
        pgid = os.getpgid(pid)
        os.killpg(pgid, signal.SIGTERM)
    except Exception:
        pass

    # Fallback — убиваем только сам процесс
    try:
        os.kill(pid, signal.SIGTERM)
    except Exception:
        pass


def stop(service):
    pid = service.get("pid")

    if not pid:
        return False

    child_pids = []
    try:
        raw = service.get("child_pids")
        if raw:
            child_pids = json.loads(raw)
    except Exception:
        pass

    try:
        if IS_WINDOWS:
            for child_pid in child_pids:
                try:
                    subprocess.call(f"taskkill /PID {child_pid} /T /F", shell=True)
                    print(f"[INFO] Killed child PID {child_pid}")
                except Exception:
                    pass
            subprocess.call(f"taskkill /PID {pid} /T /F", shell=True)

        else:
            # Сначала убиваем сохранённых детей
            for child_pid in child_pids:
                try:
                    # Пробуем убить всю group дочернего процесса
                    pgid = os.getpgid(child_pid)
                    os.killpg(pgid, signal.SIGTERM)
                    print(f"[INFO] Killed child group PGID {pgid} (PID {child_pid})")
                except ProcessLookupError:
                    pass
                except Exception:
                    # Fallback — убиваем только сам процесс
                    try:
                        os.kill(child_pid, signal.SIGTERM)
                        print(f"[INFO] Killed child PID {child_pid}")
                    except Exception:
                        pass

            # Убиваем главный процесс
            try:
                pgid = os.getpgid(pid)
                os.killpg(pgid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            except Exception:
                try:
                    os.kill(pid, signal.SIGTERM)
                except Exception:
                    pass

        return True

    except Exception as e:
        print(f"[ERROR] Failed to stop service: {e}")
        return False


def restart(service):
    stop(service)
    start(service)
