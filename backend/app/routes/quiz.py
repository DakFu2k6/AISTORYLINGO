import random
import re
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models import QuizResult, Story, User, UserVocabulary, Vocabulary
from app.models import utc_now
from app.services import progress

router = APIRouter(prefix="/quiz", tags=["Quiz"])

EXTRA_MEANINGS = [
    "A large area of open grassland.",
    "To move very quickly from one place to another.",
    "A feeling of being tired after hard work.",
    "A small round fruit with a hard seed.",
    "A person who repairs broken machines.",
    "A loud noise made by a crowd.",
]

MASTERY_UP = 20
MASTERY_DOWN = 10

class SubmitQuizRequest(BaseModel):
    user_id: str
    vocabulary_id: int
    answer: str
    kind: Literal["meaning", "blank"] = "meaning"

def mask_word(sentence: str, word: str) -> Optional[str]:
    if not sentence or not word.strip():
        return None
    pattern = re.compile(rf"(?<!\w){re.escape(word.strip())}(?!\w)", re.I)
    masked, count = pattern.subn("____", sentence)
    if count == 0:  
        masked = sentence.replace(word.strip(), "____")
        count = 1 if masked != sentence else 0
    return masked if count else None

def _meaning_question(v: Vocabulary, vocab: list[Vocabulary]) -> dict:
    wrong = list({o.meaning for o in vocab if o.id != v.id and o.meaning != v.meaning})
    random.shuffle(wrong)
    wrong = wrong[:3]
    if len(wrong) < 3:
        pool = [m for m in EXTRA_MEANINGS if m not in wrong and m != v.meaning]
        wrong += random.sample(pool, 3 - len(wrong))
    options = wrong + [v.meaning]
    random.shuffle(options)
    return {
        "vocabulary_id": v.id, "kind": "meaning", "word": v.word,
        "question": f'What does "{v.word}" mean?', "options": options,
    }


def _blank_question(v: Vocabulary, vocab: list[Vocabulary]) -> Optional[dict]:
    masked = mask_word(v.example or "", v.word)
    if not masked:
        return None
    others = list({o.word.strip() for o in vocab if o.word.strip().lower() != v.word.strip().lower()})
    if len(others) < 3:
        return None
    random.shuffle(others)
    options = others[:3] + [v.word.strip()]
    random.shuffle(options)
    return {
        "vocabulary_id": v.id, "kind": "blank",
        "word": None,  
        "question": f"Fill in the blank: {masked}", "options": options,
    }

# 1) Get the questions of a story: a mix of "meaning" and "fill in the blank"
@router.get("/story/{story_id}")
def get_quiz(story_id: int, db: Session = Depends(get_session)):
    if not db.get(Story, story_id):
        raise HTTPException(404, "Story not found.")
    vocab = db.exec(select(Vocabulary).where(Vocabulary.story_id == story_id)).all()
    if not vocab:
        raise HTTPException(404, "This story has no vocabulary to practice.")
    questions = []
    for index, v in enumerate(vocab):
        question = _blank_question(v, vocab) if index % 2 == 1 else None
        questions.append(question or _meaning_question(v, vocab))

    random.shuffle(questions)
    return {"story_id": story_id, "total": len(questions), "questions": questions}

# 2) Check one answer, update mastery, XP and streak
@router.post("/submit")
def submit_quiz(req: SubmitQuizRequest, db: Session = Depends(get_session)):
    if not db.get(User, req.user_id):
        raise HTTPException(404, "User not found. Please log in again.")
    vocab = db.get(Vocabulary, req.vocabulary_id)
    if not vocab:
        raise HTTPException(404, "Word not found.")
    expected = vocab.word.strip() if req.kind == "blank" else vocab.meaning
    is_correct = req.answer.strip().lower() == expected.strip().lower()
    db.add(QuizResult(
        user_id=req.user_id, vocabulary_id=vocab.id, story_id=vocab.story_id,
        answer=req.answer, is_correct=is_correct,
    ))
    word_progress = db.exec(
        select(UserVocabulary).where(
            UserVocabulary.user_id == req.user_id, UserVocabulary.vocabulary_id == vocab.id
        )
    ).first()
    if not word_progress:
        word_progress = UserVocabulary(user_id=req.user_id, vocabulary_id=vocab.id)
    word_progress.times_reviewed += 1
    word_progress.last_reviewed = utc_now()
    if is_correct:
        word_progress.correct_answers += 1
        word_progress.mastery_level = min(100, word_progress.mastery_level + MASTERY_UP)
    else:
        word_progress.mastery_level = max(0, word_progress.mastery_level - MASTERY_DOWN)
    db.add(word_progress)
    gained = progress.XP_CORRECT if is_correct else progress.XP_WRONG
    stats = progress.award(db, req.user_id, gained)
    db.commit()
    db.refresh(word_progress)
    return {
        "is_correct": is_correct,
        "correct_answer": expected,
        "word": vocab.word,
        "meaning": vocab.meaning,
        "meaning_vi": vocab.meaning_vi or "",
        "mastery_level": word_progress.mastery_level,
        "xp_gained": gained,
        **progress.stats_dict(stats),
    }
