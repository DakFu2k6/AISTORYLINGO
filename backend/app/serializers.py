import json

from sqlmodel import Session, func, select
from app.models import Chapter, Story, Vocabulary

def story_to_dict(s: Story) -> dict:
    return {
        "id": s.id,
        "title": s.title,
        "language": s.language,
        "level": s.level,
        "genre": s.genre,
        "topic": s.topic,
        "total_chapters": s.total_chapters,
        "status": s.status,
        "source": s.source,
        "created_at": s.created_at.isoformat(),
    }

def chapter_to_dict(c: Chapter) -> dict:
    return {
        "id": c.id,
        "chapter_number": c.chapter_number,
        "content": c.content,
        "choices": json.loads(c.choices or "[]"),
        "chosen_choice": c.chosen_choice,
    }

def vocab_to_dict(v: Vocabulary) -> dict:
    return {
        "id": v.id,
        "word": v.word,
        "pronunciation": v.pronunciation or "",
        "part_of_speech": v.part_of_speech or "",
        "meaning": v.meaning,
        "meaning_vi": v.meaning_vi or "",
        "example": v.example or "",
    }

def story_summary(db: Session, s: Story) -> dict:
    data = story_to_dict(s)
    data["chapters_done"] = db.exec(
        select(func.count()).select_from(Chapter).where(Chapter.story_id == s.id)
    ).one()
    return data
