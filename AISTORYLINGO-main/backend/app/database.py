import os
from importlib import import_module

try:
    _sqlmodel = import_module("sqlmodel")
except ModuleNotFoundError as exc:
    if exc.name != "sqlmodel":
        raise
    raise RuntimeError(
        "The 'sqlmodel' package is required. Install it with: python -m pip install sqlmodel"
    ) from exc

create_engine = _sqlmodel.create_engine
Session = _sqlmodel.Session
SQLModel = _sqlmodel.SQLModel

# Lấy DATABASE_URL từ file .env 
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Khởi tạo Engine (echo=True để log SQL query khi dev)
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session