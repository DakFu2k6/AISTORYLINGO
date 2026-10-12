import os
from sqlmodel import create_engine, Session, SQLModel  # type: ignore[import-not-found]
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

# Lấy đường dẫn kết nối Database
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Khởi tạo engine (cỗ máy kết nối). echo=True để in ra các câu lệnh SQL trên terminal cho dễ debug
engine = create_engine(DATABASE_URL, echo=True)

# Hàm này sẽ được gọi khi bật server để tự động tạo bảng
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Hàm này dùng để cấp kết nối (session) cho các API mỗi khi có người dùng gọi
def get_session():
    with Session(engine) as session:
        yield session