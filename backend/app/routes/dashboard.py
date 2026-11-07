from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, select

from app.database import get_session
from app.models import QuizResult, Story, User, UserStats, UserVocabulary, Vocabulary
from app.serializers import story_summaries
from app.services import progress

router = APIRouter(prefix="/dashboard", tags=["Progress"])

MASTERED_AT = 60
RECENT_ANSWERS = 20  

@router.get("/{user_id}")
def get_dashboard(user_id: str, words_page: int = Query(1, ge=1), stories_page: int = Query(1, ge=1), page_size: int = Query(6, ge=1, le=50), db: Session = Depends(get_session)):
    if not db.get(User, user_id):
        raise HTTPException(404, "User not found. Please log in again.")
    story_query = select(Story).where(Story.user_id == user_id)
    words_query = select(Vocabulary, UserVocabulary).join(UserVocabulary, Vocabulary.id == UserVocabulary.vocabulary_id).where(UserVocabulary.user_id == user_id)
    def count(model, *filters):
        return db.exec(select(func.count()).select_from(model).where(*filters)).one()
    total_stories = count(Story, Story.user_id == user_id)
    total_words = count(UserVocabulary, UserVocabulary.user_id == user_id)
    stories = db.exec(story_query.order_by(Story.id.desc()).offset((stories_page-1)*page_size).limit(page_size)).all()
    word_rows = db.exec(words_query.order_by(UserVocabulary.id.desc()).offset((words_page-1)*page_size).limit(page_size)).all()
    quiz_total = count(QuizResult, QuizResult.user_id == user_id)
    quiz_correct = count(QuizResult, QuizResult.user_id == user_id, QuizResult.is_correct == True)
    results = db.exec(select(QuizResult).where(QuizResult.user_id == user_id).order_by(QuizResult.id.desc()).limit(RECENT_ANSWERS)).all()
    latest = db.exec(story_query.order_by(Story.id.desc()).limit(1)).first()
    recommendation = progress.recommend_level(latest.level if latest else None, [r.is_correct for r in results])
    return {
        "pagination": {"words_total": total_words, "stories_total": total_stories, "page_size": page_size, "words_page": words_page, "stories_page": stories_page},
        "statistics": {
            "total_stories": total_stories,
            "completed_stories": count(Story, Story.user_id == user_id, Story.status == "completed"),
            "words_saved": total_words,
            "words_mastered": count(UserVocabulary, UserVocabulary.user_id == user_id, UserVocabulary.mastery_level >= MASTERED_AT),
            "quiz_total": quiz_total,
            "quiz_accuracy": round(quiz_correct / quiz_total * 100, 1) if quiz_total else 0,
            **progress.stats_dict(db.get(UserStats, user_id)),
        },
        "recommendation": recommendation,
        "words": [
            {
                "word": v.word,
                "meaning": v.meaning,
                "mastery_level": uv.mastery_level,
                "times_reviewed": uv.times_reviewed,
            }
            for v, uv in word_rows
        ],
        "stories": story_summaries(db, stories),
    }
