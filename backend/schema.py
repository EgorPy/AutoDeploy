from core.method_generator import DBField, Schema


class Services(Schema):
    __tablename__ = "services"

    id: int = DBField(primary_key=True, autoincrement=True)
    name: str
    repo: str = None
    venv_path: str = None
    child_pids: str = None
    run_command: str = None
    workdir: str = None
    pid: int = None
    autostart: int = DBField(default=0)


class Settings(Schema):
    __tablename__ = "settings"

    id: int = DBField(primary_key=True, autoincrement=True)
    key: str
    value: str = None
