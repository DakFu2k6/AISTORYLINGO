from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models import User, UserVocabulary, Vocabulary

router = APIRouter(prefix="/vocabulary", tags=["Vocabulary"])

class SaveVocabularyRequest(BaseModel):
    user_id: str
    vocabulary_id: int

@router.post("/save")
def save_vocabulary(req: SaveVocabularyRequest, db: Session = Depends(get_session)):
    if not db.get(User, req.user_id):
        raise HTTPException(404, "User not found. Please log in again.")
    if not db.get(Vocabulary, req.vocabulary_id):
        raise HTTPException(404, "Word not found.")

    saved = db.exec(
        select(UserVocabulary).where(
            UserVocabulary.user_id == req.user_id,
            UserVocabulary.vocabulary_id == req.vocabulary_id,
        )
    ).first()
    if saved:
        return {"message": "Word was already in your notebook.", "already_saved": True}

    db.add(UserVocabulary(user_id=req.user_id, vocabulary_id=req.vocabulary_id))
    db.commit()
    return {"message": "Word saved to your notebook!", "already_saved": False}

@router.get("/user/{user_id}")
def get_user_vocabulary(user_id: str, db: Session = Depends(get_session)):
    rows = db.exec(
        select(Vocabulary, UserVocabulary)
        .join(UserVocabulary, Vocabulary.id == UserVocabulary.vocabulary_id)
        .where(UserVocabulary.user_id == user_id)
        .order_by(UserVocabulary.id.desc())
    ).all()
    data = [
        {
            "vocabulary_id": v.id,
            "word": v.word,
            "meaning": v.meaning,
            "meaning_vi": v.meaning_vi or "",
            "example": v.example or "",
            "mastery_level": uv.mastery_level,
            "times_reviewed": uv.times_reviewed,
        }
        for v, uv in rows
    ]
    return {"total_words": len(data), "data": data}
