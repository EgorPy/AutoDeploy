from core.method_generator import cm, AutoDB
from core.logger import logger

from backend.schema import Services, Settings

from aiogram import Bot
import subprocess
import os

db = AutoDB(cm)


def scan_repos():
    """
    Scans MAIN_WORKDIR for Git repositories.
    Returns a list of repository paths.
    """

    main_workdir = db.select_one(Settings, key="MAIN_WORKDIR").get("value")
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

    result = db.select_one(Services, workdir=workdir)
    if not result:
        name = os.path.basename(repo_path)
        db.insert(Services, name=name, repo=repo_path, workdir=workdir)


def update_repo(path):
    result = subprocess.run(
        "git pull",
        shell=True,
        cwd=path,
        capture_output=True,
        text=True
    )
    return result.stdout + result.stderr


async def deploy(bot: Bot = None, chat_id: int = None):
    """
    1. Updates repos
    2. Restarts programs that have run_command
    """

    services = db.select(Services)
    for service in services:
        await logger.note(f"Deploying {service.get('name')}", bot=bot, chat_id=chat_id)
        workdir = service["workdir"]
        cmd = service["run_command"]
        if os.path.exists(workdir):
            result = update_repo(workdir)
            await logger.note(result, bot=bot, chat_id=chat_id)
        if cmd:
            from process_manager import restart
            restart(service)
