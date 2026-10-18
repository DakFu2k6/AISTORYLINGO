from fastapi import FastAPI
from app.database import create_db_and_tables
from app import models 

from app.routes import auth
# 1. Nhập thêm cái router truyện mình vừa viết
from app.routes import stories 

app = FastAPI(title="AI StoryLingo API", version="0.1.0")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# 2. Gắn các Router vào ứng dụng
app.include_router(auth.router)
app.include_router(stories.router) 

@app.get("/")
def root():
    return {"message": "Server AI StoryLingo đang hoạt động tốt!"}