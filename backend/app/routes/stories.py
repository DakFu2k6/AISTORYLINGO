import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.database import get_session
from app.models import Chapter, Story, User, Vocabulary
from app.serializers import chapter_to_dict, story_summary, story_to_dict, vocab_to_dict
from app.services.story_service import StoryService

router = APIRouter(prefix="/stories", tags=["Stories"])

class GenerateStoryRequest(BaseModel):
    user_id: str
    language: str
    level: str
    genre: str
    topic: str
    target_words: int = Field(5, ge=1, le=10)
    total_chapters: int = Field(3, ge=2, le=5)

class NextChapterRequest(BaseModel):
    chapter_id: int
    choice: str


# 1) Generate a new story: chapter 1 + vocabulary 
@router.post("/generate")
def generate_story(req: GenerateStoryRequest, db: Session = Depends(get_session)):
    if not db.get(User, req.user_id):
        raise HTTPException(404, "User not found. Please log in again.")
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(400, "Please enter a topic.")

    data, source = StoryService().first_chapter(
        req.language, req.level, req.genre, topic, req.target_words, req.total_chapters
    )

    story = Story(
        user_id=req.user_id, title=data.title, language=req.language, level=req.level,
        genre=req.genre, topic=topic, total_chapters=req.total_chapters, source=source,
    )
    db.add(story)
    db.commit()
    db.refresh(story)

    chapter = Chapter(
        story_id=story.id, chapter_number=1, content=data.content,
        choices=json.dumps(data.choices, ensure_ascii=False),
    )
    vocab_rows = [Vocabulary(story_id=story.id, **item.model_dump()) for item in data.vocabulary]
    db.add(chapter)
    db.add_all(vocab_rows)
    db.commit()

    db.refresh(chapter)
    for v in vocab_rows:
        db.refresh(v)

    return {
        "message": "Story created!",
        "story": story_to_dict(story),
        "chapter": chapter_to_dict(chapter),
        "vocabulary": [vocab_to_dict(v) for v in vocab_rows],
    }


# 2) The reader picks a choice -> write the next chapter 
@router.post("/{story_id}/next-chapter")
def next_chapter(story_id: int, req: NextChapterRequest, db: Session = Depends(get_session)):
    story = db.get(Story, story_id)
    if not story:
        raise HTTPException(404, "Story not found.")
    current = db.get(Chapter, req.chapter_id)
    if not current or current.story_id != story_id:
        raise HTTPException(404, "Chapter not found.")

    # Double click / page refresh: return the chapter that already exists
    existing = db.exec(
        select(Chapter).where(
            Chapter.story_id == story_id, Chapter.chapter_number == current.chapter_number + 1
        )
    ).first()
    if existing:
        return {"chapter": chapter_to_dict(existing), "story": story_to_dict(story), "source": story.source}

    if current.chapter_number >= story.total_chapters:
        raise HTTPException(400, "This story is already finished.")
    choice = req.choice.strip()
    if not choice:
        raise HTTPException(400, "Please pick a choice.")

    previous = db.exec(
        select(Chapter).where(Chapter.story_id == story_id).order_by(Chapter.chapter_number)
    ).all()
    words = [v.word for v in db.exec(select(Vocabulary).where(Vocabulary.story_id == story_id)).all()]

    number = current.chapter_number + 1
    is_last = number >= story.total_chapters
    data, source = StoryService().next_chapter(
        story.title, story.language, story.level, story.genre, story.topic,
        [c.content for c in previous], choice, number, story.total_chapters, words,
    )

    new_chapter = Chapter(
        story_id=story_id, chapter_number=number, content=data.content,
        choices=json.dumps([] if is_last else data.choices, ensure_ascii=False),
    )
    current.chosen_choice = choice
    if is_last:
        story.status = "completed"
    db.add(new_chapter)
    db.add(current)
    db.add(story)
    db.commit()
    db.refresh(new_chapter)
    db.refresh(story)

    return {"chapter": chapter_to_dict(new_chapter), "story": story_to_dict(story), "source": source}


# 3) List all stories of a user 
@router.get("/history/{user_id}")
def story_history(user_id: str, db: Session = Depends(get_session)):
    stories = db.exec(
        select(Story).where(Story.user_id == user_id).order_by(Story.id.desc())
    ).all()
    return {"data": [story_summary(db, s) for s in stories]}


# 4) Open one story again (all chapters + vocabulary) 
@router.get("/{story_id}")
def get_story(story_id: int, db: Session = Depends(get_session)):
    story = db.get(Story, story_id)
    if not story:
        raise HTTPException(404, "Story not found.")
    chapters = db.exec(
        select(Chapter).where(Chapter.story_id == story_id).order_by(Chapter.chapter_number)
    ).all()
    vocab = db.exec(select(Vocabulary).where(Vocabulary.story_id == story_id)).all()
    return {
        "story": story_to_dict(story),
        "chapters": [chapter_to_dict(c) for c in chapters],
        "vocabulary": [vocab_to_dict(v) for v in vocab],
    }
