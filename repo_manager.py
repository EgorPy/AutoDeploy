import os
import subprocess
from database import conn, get_services, get_main_workdir


def scan_repos():
    """
    Scans MAIN_WORKDIR for Git repositories.
    Returns a list of repository paths.
    """

    main_workdir = get_main_workdir()
    repos = []

    # if os.path.isdir(os.path.join(main_workdir, ".git")):
    #     repos.append(main_workdir)

    for root, dirs, files in os.walk(main_workdir):
        if ".git" in dirs:
            repos.append(root)
            dirs.clear()
    return repos


def register_repo(repo_path, workdir=None):
    if workdir is None:
        workdir = repo_path
    c = conn()
    r = c.execute("SELECT id FROM services WHERE workdir=?", (workdir,)).fetchone()
    if not r:
        name = os.path.basename(repo_path)
        c.execute(
            "INSERT INTO services (name, repo, workdir) VALUES (?,?,?)",
            (name, repo_path, workdir),
        )
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
