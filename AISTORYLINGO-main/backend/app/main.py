from fastapi import FastAPI
from app.database import create_db_and_tables

# Chú ý: import models vào để SQLModel nhận diện được các bảng trước khi tạo
from app import models 

app = FastAPI(title="AI StoryLingo API", version="0.1.0")

# Sự kiện này chạy ngay khi server vừa bật lên
@app.on_event("startup")
def on_startup():
    print("Đang kết nối Database và tạo bảng...")
    create_db_and_tables()
    print("Tạo bảng thành công! Các bảng đã có trong Supabase.")

@app.get("/")
def root():
    return {"message": "AI StoryLingo API is running"}