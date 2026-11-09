import logging
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  
from app.database import create_db_and_tables
from app.routes import auth, dashboard, quiz, stories, vocabulary, admin
from app.security import protect_learning
from app.services.story_service import StoryService, get_story_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    info = get_story_service().describe()
    if info["configured"]:
        logging.getLogger("storylingo.ai").info(
            "AI ready: backend=%s model=%s", info["backend"], info["model"]
        )
    else:
        logging.getLogger("storylingo.ai").warning("AI NOT active: %s", info["last_error"])
    yield

app = FastAPI(title="AI StoryLingo API", version="1.1.0", lifespan=lifespan)

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500,http://localhost:5501,http://127.0.0.1:5501,http://localhost:3000,http://127.0.0.1:3000").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials="*" not in origins,  
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(stories.router, dependencies=[Depends(protect_learning)])
app.include_router(vocabulary.router, dependencies=[Depends(protect_learning)])
app.include_router(quiz.router, dependencies=[Depends(protect_learning)])
app.include_router(dashboard.router, dependencies=[Depends(protect_learning)])

@app.get("/", tags=["Health"])
def root():
    return {"message": "AI StoryLingo API is running. See /docs for all endpoints."}

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

@app.get("/health/ai", tags=["Health"])
def health_ai(probe: bool = False, ai: StoryService = Depends(get_story_service)):
    info = ai.describe()
    if probe:
        info["probe"] = ai.probe()
    return info
