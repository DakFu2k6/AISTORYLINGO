import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Request
from sqlmodel import Session, select
from app.database import get_session
from app.models import AuthToken, User, Story, Vocabulary

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def issue(db, user_id, purpose="session", minutes=1440):
    raw = secrets.token_urlsafe(32)
    db.add(AuthToken(digest=digest(raw), user_id=user_id, purpose=purpose,
                     expires_at=datetime.now(timezone.utc) + timedelta(minutes=minutes)))
    db.commit()
    return raw

def token_row(db, raw, purpose="session"):
    row = db.get(AuthToken, digest(raw))
    if not row or row.purpose != purpose:
        raise HTTPException(401, "Session or link is invalid. Please log in again.")
    expiry = row.expires_at.replace(tzinfo=timezone.utc) if row.expires_at.tzinfo is None else row.expires_at
    if expiry <= datetime.now(timezone.utc):
        raise HTTPException(401, "Session or link expired. Please log in again.")
    return row

def current_user(request: Request, db: Session = Depends(get_session)):
    scheme, _, raw = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not raw:
        raise HTTPException(401, "Please log in again.")
    row = token_row(db, raw)
    user = db.get(User, row.user_id)
    if not user:
        raise HTTPException(401, "Please log in again.")
    return user

def admin_user(user: User = Depends(current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Administrator access required.")
    return user

async def protect_learning(request: Request, user: User = Depends(current_user), db: Session = Depends(get_session)):
    try:
        body = await request.json() if request.method in {"POST", "PATCH", "PUT"} else {}
    except ValueError:
        raise HTTPException(422, "Request body must be valid JSON.")
    if not isinstance(body, dict):
        raise HTTPException(422, "Request body must be an object.")
    supplied = body.get("user_id") or request.path_params.get("user_id") or request.query_params.get("user_id")
    if supplied and supplied != user.id:
        raise HTTPException(403, "You cannot access another learner's data.")
    story_id = request.path_params.get("story_id")
    word_id = body.get("vocabulary_id")
    if word_id is not None:
        word = db.get(Vocabulary, word_id)
        if not word:
            raise HTTPException(404, "Word not found.")
        story_id = word.story_id
    if story_id is not None:
        story = db.get(Story, story_id)
        if not story or story.user_id != user.id:
            raise HTTPException(404, "Story not found.")
