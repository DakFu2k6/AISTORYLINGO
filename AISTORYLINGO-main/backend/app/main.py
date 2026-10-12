from fastapi import FastAPI
from pydantic import BaseModel

from app.services.story_service import StoryService

app = FastAPI(title="AI StoryLingo API", version="0.1.0")

class StoryRequest(BaseModel):
    language: str
    level: str
    genre: str
    topic: str
    target_words: int = 5

@app.get("/")
def root():
    return {"message": "AI StoryLingo API is running"}

@app.post("/generate-story")
def generate_story(request: StoryRequest):
    service = StoryService()
    story = service.generate_story(
        language=request.language,
        level=request.level,
        genre=request.genre,
        topic=request.topic,
        target_words=request.target_words
    )
    return story.model_dump()