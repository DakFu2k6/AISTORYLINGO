from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models 
from app.database import create_db_and_tables
from app.routes import auth, dashboard, quiz, stories, vocabulary

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="AI StoryLingo API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(stories.router)
app.include_router(vocabulary.router)
app.include_router(quiz.router)
app.include_router(dashboard.router)

@app.get("/", tags=["Health"])
def root():
    return {"message": "AI StoryLingo API is running. See /docs for all endpoints."}