from aiogram import Bot, Dispatcher, types
from database import get_services, update_command, update_workdir, get_main_workdir, set_main_workdir, init_db
from repo_manager import scan_repos, register_repo
from process_manager import start, stop, restart
from config import TOKEN
import os

init_db()

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


def find_service(sid):
    services = get_services()
    for s in services:
        if s[0] == sid:
            return s
    return None


@dp.message_handler(commands=["help"])
async def help_cmd(message: types.Message):
    text = """
Available commands:

/help — show this help message
/services — list all registered services

/start <id> — start a service
/stop <id> — stop a service
/restart <id> — restart a service

/setcmd <id> <command> — change the run command for a service
/setwd <id> <path> — change the working directory for a service

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


@dp.message_handler(commands=["services"])
async def list_services(message: types.Message):
    services = get_services()
    text = "Services:\n"
    for s in services:
        text += f"{s[0]} | {s[1]}\n"
    await message.reply(text)


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

    set_main_workdir(path)

    repos = scan_repos()
    for r in repos:
        register_repo(r)

    await message.reply(
        f"Main working directory updated to:\n{path}\nFound and registered {len(repos)} repositories."
    )


@dp.message_handler(commands=["start"])
async def start_service_cmd(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /start <id>")
        return
    sid = int(parts[1])
    s = find_service(sid)
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
    s = find_service(sid)
    if not s:
        await message.reply("Service not found")
        return
    stop(s)
    await message.reply("Service stopped")


@dp.message_handler(commands=["restart"])
async def restart_service_cmd(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /restart <id>")
        return
    sid = int(parts[1])
    s = find_service(sid)
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
    sid = int(parts[1])
    cmd = parts[2]
    s = find_service(sid)
    if not s:
        await message.reply("Service not found")
        return
    update_command(sid, cmd)
    await message.reply("Run command updated")


@dp.message_handler(commands=["setwd"])
async def setwd_service_cmd(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply("Usage: /setwd <id> <path>")
        return
    sid = int(parts[1])
    wd = parts[2]
    s = find_service(sid)
    if not s:
        await message.reply("Service not found")
        return
    update_workdir(sid, wd)
    await message.reply("Working directory updated")


@dp.message_handler(commands=["getwd"])
async def get_workdir(message: types.Message):
    wd = get_main_workdir()
    await message.reply(f"Current main working directory:\n{wd}")


@dp.message_handler(commands=["setwd"])
async def set_workdir(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Usage: /setwd <path>")
        return
    path = parts[1]
    if not os.path.exists(path):
        await message.reply("Directory does not exist")
        return
    set_main_workdir(path)
    repos = scan_repos()
    for r in repos:
        register_repo(r)
    await message.reply(f"Main working directory updated to:\n{path}\nFound {len(repos)} repositories")


if __name__ == "__main__":
    from aiogram import executor

    print("Telegram bot starting...")
    repos = scan_repos()
    for r in repos:
        register_repo(r, workdir=r)
    print(f"Found and registered {len(repos)} repositories on startup")
    executor.start_polling(dp, skip_updates=True)
