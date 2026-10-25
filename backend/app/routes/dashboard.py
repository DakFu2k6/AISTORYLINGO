from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import QuizResult, Story, User, UserVocabulary, Vocabulary
from app.serializers import story_summary

router = APIRouter(prefix="/dashboard", tags=["Progress"])

MASTERED_AT = 60  

@router.get("/{user_id}")
def get_dashboard(user_id: str, db: Session = Depends(get_session)):
    if not db.get(User, user_id):
        raise HTTPException(404, "User not found. Please log in again.")

    stories = db.exec(select(Story).where(Story.user_id == user_id).order_by(Story.id.desc())).all()

    word_rows = db.exec(
        select(Vocabulary, UserVocabulary)
        .join(UserVocabulary, Vocabulary.id == UserVocabulary.vocabulary_id)
        .where(UserVocabulary.user_id == user_id)
        .order_by(UserVocabulary.id.desc())
    ).all()

    results = db.exec(select(QuizResult).where(QuizResult.user_id == user_id)).all()
    quiz_total = len(results)
    quiz_correct = sum(1 for r in results if r.is_correct)

    return {
        "statistics": {
            "total_stories": len(stories),
            "completed_stories": sum(1 for s in stories if s.status == "completed"),
            "words_saved": len(word_rows),
            "words_mastered": sum(1 for _, uv in word_rows if uv.mastery_level >= MASTERED_AT),
            "quiz_total": quiz_total,
            "quiz_accuracy": round(quiz_correct / quiz_total * 100, 1) if quiz_total else 0,
        },
        "words": [
            {
                "word": v.word,
                "meaning": v.meaning,
                "mastery_level": uv.mastery_level,
                "times_reviewed": uv.times_reviewed,
            }
            for v, uv in word_rows
        ],
        "stories": [story_summary(db, s) for s in stories],
    }
