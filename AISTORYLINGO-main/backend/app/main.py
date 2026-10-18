from fastapi import FastAPI
from app.database import create_db_and_tables
from app import models 

# 1. Nhập cái router auth mình vừa viết
from app.routes import auth 

app = FastAPI(title="AI StoryLingo API", version="0.1.0")

@app.on_event("startup")
def on_startup():
    print("Đang khởi động Database...")
    create_db_and_tables()
    print("Database đã sẵn sàng!")

# 2. Gắn router auth vào ứng dụng chính
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "Server AI StoryLingo đang hoạt động tốt!"}