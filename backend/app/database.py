import logging
import os

from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

log = logging.getLogger("storylingo.db")

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR.parent / ".env")
load_dotenv(BACKEND_DIR / ".env")  

def _database_url() -> str:
    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url:
        return f"sqlite:///{BACKEND_DIR / 'storylingo.db'}"
    if url.startswith("postgres://"):  
        url = url.replace("postgres://", "postgresql://", 1)
    return url

DATABASE_URL = _database_url()
IS_SQLITE = DATABASE_URL.startswith("sqlite")

log.info("Database backend: %s", "SQLite" if IS_SQLITE else DATABASE_URL.split(":", 1)[0])

if IS_SQLITE:
    engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,   
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
    )

ADDED_COLUMNS = {
    "users": {
        "role": "VARCHAR NOT NULL DEFAULT 'user'",
        "google_sub": "VARCHAR",
        "username": "VARCHAR",
    },
    "user_vocabulary": {"last_reviewed": "TIMESTAMP"},
    "stories": {"context": "TEXT"},
}

def ensure_columns(target: Engine | None = None) -> list[str]:
    target = target or engine
    added: list[str] = []
    inspector = inspect(target)
    with target.begin() as conn:
        for table, columns in ADDED_COLUMNS.items():
            if not inspector.has_table(table):
                continue
            existing = {c["name"] for c in inspector.get_columns(table)}
            for name, ddl in columns.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
                    added.append(f"{table}.{name}")
        if inspector.has_table("users"):
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_subject ON users (google_sub)"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)"))
    return added

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    for item in ensure_columns():
        log.info("Database upgraded: added column %s", item)

def get_session():
    with Session(engine) as session:
        yield session
