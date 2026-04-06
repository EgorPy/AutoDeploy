from core.method_generator import AutoDB, cm
from core.logger import logger

from backend.schema import Services, Settings

from repo_manager import scan_repos, register_repo, deploy
from process_manager import start, stop, restart
from aiogram import Bot, Dispatcher, types
from config import TOKEN
import os

db = AutoDB(cm)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


def get_service(service_id):
    services = db.select(Services)
    for s in services:
        if s["id"] == service_id:
            return s
    return None


@dp.message_handler(commands=["help"])
async def help_cmd(message: types.Message):
    text = """
Available commands:

/help — show this help message
/services — list all registered services
/add_service <path> — add service
/remove_service <id> — remove service
/deploy — update and deploy all services

/start <id> — start a service
/stop <id> — stop a service
/restart <id> — restart a service

/setcmd <id> <command> — change the run command for a service
/setwd <id> <path> — change the working directory for a service
/setvenv <id> <venv_path> — set venv path for a service

/getwd — show current main working directory
/setmainwd <path> — set main working directory (bot will rescan and register repositories)

Examples:

/start 1
/restart 2
/setcmd 1 python3.9 bot.py
/setwd 1 /root/midjourney
/getwd
/setmainwd /home/user/projects
"""
    await message.reply(text)


@dp.message_handler(commands=["add_service"])
async def add_service_cmd(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Usage: /add_service <path>")
        return
    path = parts[1].strip()
    if not os.path.exists(path):
        await message.reply("Directory does not exist")
        return
    name = os.path.basename(path)
    existing = db.select(Services)
    for s in existing:
        if s["workdir"] == path:
            await message.reply("Service already exists")
            return
    db.insert(
        Services,
        name=name,
        repo=name,
        run_command="",
        workdir=path,
        pid=None
    )
    await message.reply(f"Service added:\n{name}\n{path}")


@dp.message_handler(commands=["remove_service"])
async def remove_service_cmd(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /remove_service <id>")
        return
    service_id = int(parts[1])
    service = get_service(service_id)
    if not service:
        await message.reply("Service not found")
        return
    stop(service)
    db.delete(Services, id=service_id)
    await message.reply(f"Service {service_id} removed")


@dp.message_handler(commands=["services"])
async def list_services(message: types.Message):
    services = db.select(Services)
    text = "Services:\n"
    text += "id, name, run_command, workdir, pid\n"
    text += "<code>"
    for s in services:
        text += f"{s['id']} | {s['name']} | {s['run_command']} | {s['workdir']} | {s['pid']}\n\n"
    text += "</code>"
    await message.reply(text, parse_mode="HTML")


@dp.message_handler(commands=["setmainwd"])
async def set_main_workdir_cmd(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Usage: /setmainwd <path>")
        return

    path = parts[1].strip()
    if not os.path.exists(path):
        await message.reply("Directory does not exist")
        return

    db.delete(Settings, key="MAIN_WORKDIR")
    db.insert(Settings, key="MAIN_WORKDIR", value=path)

    repos = scan_repos()
    for r in repos:
        register_repo(r)

    await message.reply(
        f"Main working directory updated to:\n{path}\nFound and registered {len(repos)} repositories."
    )
    await message.answer("\n".join(repos))


@dp.message_handler(commands=["start"])
async def start_service_cmd(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /start <id>")
        return
    sid = int(parts[1])
    s = get_service(sid)
    if not s:
        await message.reply("Service not found")
        return
    start(s)
    await message.reply("Service started")


@dp.message_handler(commands=["stop"])
async def stop_service_cmd(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /stop <id>")
        return
    sid = int(parts[1])
    service = get_service(sid)
    if not service:
        await message.reply("Service not found")
        return
    stop(service)
    await message.reply("Service stopped")


@dp.message_handler(commands=["restart"])
async def restart_service_cmd(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /restart <id>")
        return
    sid = int(parts[1])
    s = get_service(sid)
    if not s:
        await message.reply("Service not found")
        return
    restart(s)
    await message.reply("Service restarted")


@dp.message_handler(commands=["setcmd"])
async def setcmd_service_cmd(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply("Usage: /setcmd <id> <command>")
        return
    service_id = int(parts[1])
    command = parts[2]
    service = get_service(service_id)
    if not service:
        await message.reply("Service not found")
        return
    db.update(Services, {"run_command": command}, {"id": service_id})
    await message.reply("Run command updated")


@dp.message_handler(commands=["setwd"])
async def setwd_service_cmd(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply("Usage: /setwd <id> <path>")
        return
    service_id = int(parts[1])
    workdir = parts[2]
    service = get_service(service_id)
    if not service:
        await message.reply("Service not found")
        return
    db.update(Services, {"workdir": workdir}, {"id": service_id})
    await message.reply("Working directory updated")


@dp.message_handler(commands=["getwd"])
async def get_service_workdir(message: types.Message):
    parts = message.text.split()
    if len(parts) == 1:
        main_wd = db.select_one(Settings, key="MAIN_WORKDIR").get("value")
        await message.reply(f"Current main working directory:\n{main_wd}")
        return
    try:
        service_id = int(parts[1])
    except ValueError:
        await message.reply("Service ID must be a number")
        return
    service = get_service(service_id)
    if not service:
        await message.reply("Service not found")
        return
    workdir = service.get("workdir")
    await message.reply(f"Service {service_id} working directory:\n{workdir}")


@dp.message_handler(commands=["setvenv"])
async def setvenv_cmd(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply("Usage: /setvenv <id> <venv_path>")
        return
    service_id = int(parts[1])
    venv = parts[2].strip()
    service = get_service(service_id)
    if not service:
        await message.reply("Service not found")
        return
    db.update(Services, {"venv_path": venv}, {"id": service_id})
    await message.reply(f"Venv path updated to:\n{venv}")


@dp.message_handler(commands=["deploy"])
async def deploy_services(message: types.Message):
    await message.answer("Deploying...")
    await deploy(bot, message.chat.id)


if __name__ == "__main__":
    from aiogram import executor

    print("Telegram bot starting...")
    # repos = scan_repos()
    # for r in repos:
    #     register_repo(r, workdir=r)
    # print(f"Found and registered {len(repos)} repositories on startup")
    executor.start_polling(dp, skip_updates=True)
