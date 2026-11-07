import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlmodel import Session, select

from app.database import get_session
from app.models import Chapter, Story, User, Vocabulary
from app.serializers import chapter_to_dict, story_summaries, story_to_dict, vocab_to_dict
from app.services import progress, rate_limit
from app.services.story_service import StoryService, get_story_service

router = APIRouter(prefix="/stories", tags=["Stories"])

class GenerateStoryRequest(BaseModel):
    user_id: str
    language: str = Field(max_length=40)
    level: Literal["A1", "A2", "B1", "B2", "C1"]
    genre: str = Field(max_length=40)
    topic: str = Field(max_length=80)
    target_words: int = Field(5, ge=1, le=10)
    total_chapters: int = Field(3, ge=2, le=5)

class NextChapterRequest(BaseModel):
    user_id: str
    chapter_id: int
    choice: str = Field(max_length=200)

def _own_story(db: Session, story_id: int, user_id: str) -> Story:
    story = db.get(Story, story_id)
    if not story or story.user_id != user_id:
        raise HTTPException(404, "Story not found.")
    return story


# 1) Generate a new story: chapter 1 + vocabulary
@router.post("/generate")
def generate_story(
    req: GenerateStoryRequest,
    db: Session = Depends(get_session),
    ai: StoryService = Depends(get_story_service),
):
    if not db.get(User, req.user_id):
        raise HTTPException(404, "User not found. Please log in again.")
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(400, "Please enter a topic.")
    wait = rate_limit.hit(req.user_id)
    if wait:
        raise HTTPException(
            429,
            f"You reached the limit of {rate_limit.limit_per_hour()} new stories per hour. "
            f"Please try again in {max(1, wait // 60)} minute(s).",
        )
    result = ai.first_chapter(
        req.language, req.level, req.genre, topic, req.target_words, req.total_chapters
    )
    data = result.data
    story = Story(
        user_id=req.user_id, title=data.title, language=req.language, level=req.level,
        genre=req.genre, topic=topic, total_chapters=req.total_chapters, source=result.source,
        context=json.dumps({"characters": data.characters, "setting": data.setting}, ensure_ascii=False),
    )
    db.add(story)
    db.commit()
    db.refresh(story)
    chapter = Chapter(
        story_id=story.id, chapter_number=1, content=data.content,
        choices=json.dumps(data.choices, ensure_ascii=False),
    )
    vocab_rows = [
        Vocabulary(story_id=story.id, **item.model_dump(exclude={"id"})) for item in data.vocabulary
    ]
    db.add(chapter)
    db.add_all(vocab_rows)
    progress.award(db, req.user_id, 0)  
    db.commit()
    db.refresh(chapter)
    for v in vocab_rows:
        db.refresh(v)
    return {
        "message": "Story created!",
        "story": story_to_dict(story),
        "chapter": chapter_to_dict(chapter),
        "vocabulary": [vocab_to_dict(v) for v in vocab_rows],
        "fallback_reason": result.fallback_reason,
    }

# 2) The reader picks a choice -> write the next chapter
@router.post("/{story_id}/next-chapter")
def next_chapter(
    story_id: int,
    req: NextChapterRequest,
    db: Session = Depends(get_session),
    ai: StoryService = Depends(get_story_service),
):
    story = _own_story(db, story_id, req.user_id)
    current = db.get(Chapter, req.chapter_id)
    if not current or current.story_id != story_id:
        raise HTTPException(404, "Chapter not found.")
    existing = db.exec(
        select(Chapter).where(
            Chapter.story_id == story_id, Chapter.chapter_number == current.chapter_number + 1
        )
    ).first()
    if existing:
        return {"chapter": chapter_to_dict(existing), "story": story_to_dict(story),
                "source": story.source, "fallback_reason": None}

    if current.chapter_number >= story.total_chapters:
        raise HTTPException(400, "This story is already finished.")
    choice = req.choice.strip()
    offered = json.loads(current.choices or "[]")
    if choice not in offered:
        raise HTTPException(400, "Please pick one of the choices shown.")
    previous = db.exec(
        select(Chapter).where(Chapter.story_id == story_id).order_by(Chapter.chapter_number)
    ).all()
    words = [v.word for v in db.exec(select(Vocabulary).where(Vocabulary.story_id == story_id)).all()]
    try:
        context = json.loads(story.context) if story.context else None
    except ValueError:
        context = None
    number = current.chapter_number + 1
    is_last = number >= story.total_chapters
    result = ai.next_chapter(
        story.title, story.language, story.level, story.genre, story.topic,
        [c.content for c in previous], choice, number, story.total_chapters, words, context,
    )
    new_chapter = Chapter(
        story_id=story_id, chapter_number=number, content=result.data.content,
        choices=json.dumps([] if is_last else result.data.choices, ensure_ascii=False),
    )
    current.chosen_choice = choice
    if is_last:
        story.status = "completed"
        progress.award(db, story.user_id, progress.XP_STORY_COMPLETED)
    db.add(new_chapter)
    db.add(current)
    db.add(story)
    db.commit()
    db.refresh(new_chapter)
    db.refresh(story)
    return {
        "chapter": chapter_to_dict(new_chapter),
        "story": story_to_dict(story),
        "source": result.source,
        "fallback_reason": result.fallback_reason,
    }

# 3) List all stories of a user
@router.get("/history/{user_id}")
def story_history(user_id: str, page: int = Query(1, ge=1), page_size: int = Query(6, ge=1, le=50), db: Session = Depends(get_session)):
    stories = db.exec(
        select(Story).where(Story.user_id == user_id).order_by(Story.id.desc()).offset((page-1)*page_size).limit(page_size)
    ).all()
    return {"data": story_summaries(db, stories), "page": page, "page_size": page_size,
            "total": db.exec(select(func.count()).select_from(Story).where(Story.user_id == user_id)).one()}

# 4) Open one story again (all chapters + vocabulary). Only the owner may read it.
@router.get("/{story_id}")
def get_story(story_id: int, user_id: str = Query(...), db: Session = Depends(get_session)):
    story = _own_story(db, story_id, user_id)
    chapters = db.exec(
        select(Chapter).where(Chapter.story_id == story_id).order_by(Chapter.chapter_number)
    ).all()
    vocab = db.exec(select(Vocabulary).where(Vocabulary.story_id == story_id)).all()
    return {
        "story": story_to_dict(story),
        "chapters": [chapter_to_dict(c) for c in chapters],
        "vocabulary": [vocab_to_dict(v) for v in vocab],
    }
