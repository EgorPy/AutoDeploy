import subprocess
import os
import signal
from database import update_pid


def start(service):
    service_id, name, repo, cmd, wd, pid = service

    out = f"{name}.out"

    p = subprocess.Popen(
        f"nohup {cmd} > {out} 2>&1 & echo $!",
        shell=True,
        cwd=wd,
        stdout=subprocess.PIPE
    )

    pid = int(p.stdout.read().decode().strip())
    update_pid(service_id, pid)


def stop(service):
    pid = service[5]
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except:
            pass


def restart(service):
    stop(service)
    start(service)
