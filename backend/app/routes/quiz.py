import random

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models import QuizResult, Story, User, UserVocabulary, Vocabulary

router = APIRouter(prefix="/quiz", tags=["Quiz"])

EXTRA_MEANINGS = [
    "A large area of open grassland.",
    "To move very quickly from one place to another.",
    "A feeling of being tired after hard work.",
    "A small round fruit with a hard seed.",
    "A person who repairs broken machines.",
    "A loud noise made by a crowd.",
]

class SubmitQuizRequest(BaseModel):
    user_id: str
    vocabulary_id: int
    answer: str

# 1) Get the questions of a story 
@router.get("/story/{story_id}")
def get_quiz(story_id: int, db: Session = Depends(get_session)):
    if not db.get(Story, story_id):
        raise HTTPException(404, "Story not found.")
    vocab = db.exec(select(Vocabulary).where(Vocabulary.story_id == story_id)).all()
    if not vocab:
        raise HTTPException(404, "This story has no vocabulary to practice.")

    questions = []
    for v in vocab:
        wrong = [o.meaning for o in vocab if o.id != v.id and o.meaning != v.meaning]
        random.shuffle(wrong)
        wrong = wrong[:3]
        if len(wrong) < 3:
            pool = [m for m in EXTRA_MEANINGS if m not in wrong and m != v.meaning]
            wrong += random.sample(pool, 3 - len(wrong))

        options = wrong + [v.meaning]
        random.shuffle(options)
        questions.append({
            "vocabulary_id": v.id,
            "word": v.word,
            "question": f'What does "{v.word}" mean?',
            "options": options,
        })

    random.shuffle(questions)
    return {"story_id": story_id, "total": len(questions), "questions": questions}


# 2) Check one answer and update the user's progress 
@router.post("/submit")
def submit_quiz(req: SubmitQuizRequest, db: Session = Depends(get_session)):
    if not db.get(User, req.user_id):
        raise HTTPException(404, "User not found. Please log in again.")
    vocab = db.get(Vocabulary, req.vocabulary_id)
    if not vocab:
        raise HTTPException(404, "Word not found.")

    is_correct = req.answer.strip().lower() == vocab.meaning.strip().lower()

    db.add(QuizResult(
        user_id=req.user_id, vocabulary_id=vocab.id, story_id=vocab.story_id,
        answer=req.answer, is_correct=is_correct,
    ))

    # Every practiced word goes into the notebook automatically
    progress = db.exec(
        select(UserVocabulary).where(
            UserVocabulary.user_id == req.user_id, UserVocabulary.vocabulary_id == vocab.id
        )
    ).first()
    if not progress:
        progress = UserVocabulary(user_id=req.user_id, vocabulary_id=vocab.id)

    progress.times_reviewed += 1
    if is_correct:
        progress.correct_answers += 1
        progress.mastery_level = min(100, progress.mastery_level + 20)
    else:
        progress.mastery_level = max(0, progress.mastery_level - 10)
    db.add(progress)
    db.commit()
    db.refresh(progress)

    return {
        "is_correct": is_correct,
        "correct_answer": vocab.meaning,
        "meaning_vi": vocab.meaning_vi or "",
        "mastery_level": progress.mastery_level,
    }
