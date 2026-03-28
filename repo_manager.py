import os
import subprocess
from database import conn, get_services, get_main_workdir


def scan_repos():
    """
        Scans MAIN_WORKDIR for Git repositories.
        Returns a list of repository paths.
        """

    MAIN_WORKDIR = get_main_workdir()
    repos = []
    for root, dirs, files in os.walk(MAIN_WORKDIR):
        if ".git" in dirs:
            repos.append(root)
            dirs.clear()
    return repos


def register_repo(path):
    c = conn()
    r = c.execute("SELECT id FROM services WHERE workdir=?", (path,)).fetchone()
    if not r:
        name = os.path.basename(path)
        c.execute("""
            INSERT INTO services (name, repo, run_command, workdir, pid, autostart)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, name, "", path, None, 0))
        c.commit()
    c.close()


def update_repo(path):
    subprocess.call("git pull", shell=True, cwd=path)


def deploy():
    """
    1. Scans MAIN_WORKDIR
    2. Registers new repos in db
    3. Updates repos
    4. Restarts programs that have run_command
    """

    repos = scan_repos()
    for r in repos:
        register_repo(r)

    services = get_services()
    for s in services:
        workdir = s[4]
        cmd = s[3]
        if os.path.exists(workdir):
            update_repo(workdir)
        if cmd:
            from process_manager import restart
            restart(s)
