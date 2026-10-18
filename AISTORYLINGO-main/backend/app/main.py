from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_db_and_tables
from app import models 
from app.routes import auth, stories, vocabulary, quiz, dashboard

app = FastAPI(title="AI StoryLingo API", version="0.1.0")

# Chống lỗi CORS khi Frontend gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép mọi nguồn gọi đến. Khi làm đồ án cứ để "*" cho dễ test.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Gắn các router
app.include_router(auth.router)
app.include_router(stories.router)
app.include_router(vocabulary.router)
app.include_router(quiz.router)
app.include_router(dashboard.router)

@app.get("/")
def root():
    return {"message": "Server AI StoryLingo đang hoạt động tốt!"}