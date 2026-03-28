# AutoDeploy

A lightweight system for **automatic deployment**, **process management**, and **Telegram-based control** of Python programs on
your server.

## Features

* Automatic deployment on GitHub push
* Start, stop, and restart programs via Telegram
* Customize run commands per program
* Set working directory for each program
* Log output of all programs to individual `.out` files
* Centralized management via SQLite database

---

## Architecture

| Component            | Purpose                                          |
|----------------------|--------------------------------------------------|
| `telegram_bot.py`    | Telegram interface for managing services         |
| `webhook.py`         | Receives GitHub webhooks and triggers deploy     |
| `repo_manager.py`    | Pulls updates from repositories                  |
| `process_manager.py` | Handles starting, stopping, restarting processes |
| `database.py`        | Stores services configuration in SQLite          |

---

## Database

**Table: `services`**

| Column        | Description                |
|---------------|----------------------------|
| `id`          | Service ID                 |
| `name`        | Service name               |
| `repo`        | Repository name            |
| `run_command` | Command to run the program |
| `workdir`     | Working directory          |
| `pid`         | Process ID                 |
| `autostart`   | Flag for automatic start   |

---

## Getting Started

Понял. Тогда в README нужно сделать универсально: **любая директория**, в которой находится репозиторий, и путь задаётся в
конфигурации каждого сервиса через `workdir`.

Вот исправленный раздел:

---

### Repository Setup

Each service can reside in **any directory** on the server.

When adding a service, specify:

* **Repository location** — the working directory (`workdir`) of the program
* **Run command** — how to start the program from that directory

Example structure (services may be anywhere):

```text
/root/bot/bot.py
/home/user/worker/worker.py
/opt/parser/parser.py
```

The system uses the `workdir` of each service to run `git pull` and launch the program, so you have full flexibility in where
repositories are stored.

---

Если хочешь, я могу сразу переписать **весь README на английском в Markdown с этим исправлением**, чтобы он был готов к
использованию. Сделать?


---

### Running the System

Run the webhook and Telegram bot with Python 3.9:

```bash
python3.9 webhook.py
python3.9 telegram_bot.py
```

Or in the background using `nohup`:

```bash
nohup python3.9 webhook.py > webhook.out 2>&1 &
nohup python3.9 telegram_bot.py > bot.out 2>&1 &
```

---

### GitHub Webhook

1. Go to **Settings → Webhooks → Add webhook** in your GitHub repo
2. Payload URL: `http://SERVER_IP:9000`
3. Content type: `application/json`
4. Trigger: **Push events**

---

## Telegram Commands

| Command                  | Description                            |
|--------------------------|----------------------------------------|
| `/help`                  | Show available commands                |
| `/services`              | List all services                      |
| `/start <id>`            | Start a service                        |
| `/stop <id>`             | Stop a service                         |
| `/restart <id>`          | Restart a service                      |
| `/setcmd <id> <command>` | Change run command for a service       |
| `/setwd <id> <path>`     | Change working directory for a service |

**Example:**

```
/start 1
/restart 2
/setcmd 1 python3.9 bot.py
/setwd 1 /root/repos/midjourney
```

---

## Logs

Each program logs to its own `.out` file:

```
bot.out
worker.out
parser.out
```

View logs in real-time:

```bash
tail -f bot.out
```

---

## Notes

* Ensure your server allows incoming connections for GitHub webhook (consider firewall, NAT, or reverse proxy).
* Telegram bot sends notifications about service management.
* Commands can be customized per service for flexibility.

---
