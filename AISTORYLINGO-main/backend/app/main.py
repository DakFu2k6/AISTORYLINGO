from fastapi import FastAPI
from app.database import create_db_and_tables
from app import models 

from app.routes import auth
from app.routes import stories
from app.routes import vocabulary 

app = FastAPI(title="AI StoryLingo API", version="0.1.0")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(auth.router)
app.include_router(stories.router)
# 2. Gắn router từ vựng vào ứng dụng
app.include_router(vocabulary.router) 

@app.get("/")
def root():
    return {"message": "Server AI StoryLingo đang hoạt động tốt!"}