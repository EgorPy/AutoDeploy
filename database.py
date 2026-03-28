import os
import sqlite3

DB = "database.db"


def conn():
    return sqlite3.connect(DB)


def init_db():
    c = conn()
    c.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        repo TEXT,
        run_command TEXT,
        workdir TEXT,
        pid INTEGER,
        autostart INTEGER DEFAULT 0
    )
    """)
    c.commit()
    c.close()


init_db()


def get_services():
    c = conn()
    r = c.execute("""
        SELECT id, name, repo, run_command, workdir, pid 
        FROM services
    """).fetchall()
    c.close()
    return r


def update_pid(service_id, pid):
    c = conn()
    c.execute("UPDATE services SET pid=? WHERE id=?", (pid, service_id))
    c.commit()
    c.close()


def update_command(service_id, cmd):
    c = conn()
    c.execute("UPDATE services SET run_command=? WHERE id=?", (cmd, service_id))
    c.commit()
    c.close()


def update_workdir(service_id, wd):
    c = conn()
    c.execute("UPDATE services SET workdir=? WHERE id=?", (wd, service_id))
    c.commit()
    c.close()


def init_db():
    c = conn()
    c.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        repo TEXT,
        run_command TEXT,
        workdir TEXT,
        pid INTEGER,
        autostart INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    r = c.execute("SELECT value FROM settings WHERE key='MAIN_WORKDIR'").fetchone()
    if not r:
        c.execute("INSERT INTO settings (key,value) VALUES (?,?)", ("MAIN_WORKDIR", os.getcwd()))
    c.commit()
    c.close()


def get_main_workdir():
    c = conn()
    r = c.execute("SELECT value FROM settings WHERE key='MAIN_WORKDIR'").fetchone()
    c.close()
    return r[0] if r else "/root"


def set_main_workdir(path):
    c = conn()
    c.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", ("MAIN_WORKDIR", path))
    c.commit()
    c.close()
