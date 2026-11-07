import json

from typing import Sequence
from sqlmodel import Session, col, func, select
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

def story_summaries(db: Session, stories: Sequence[Story]) -> list[dict]:
    ids = [s.id for s in stories]
    counts: dict[int, int] = {}
    if ids:
        rows = db.exec(
            select(Chapter.story_id, func.count())
            .where(col(Chapter.story_id).in_(ids))
            .group_by(Chapter.story_id)
        ).all()
        counts = {story_id: n for story_id, n in rows}
    return [{**story_to_dict(s), "chapters_done": counts.get(s.id, 0)} for s in stories]

def story_summary(db: Session, s: Story) -> dict:
    return story_summaries(db, [s])[0]
