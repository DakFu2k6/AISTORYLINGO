import os
from typing import Optional
import re
import uuid
import secrets
import logging
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from app.database import get_session
from app.models import User, AuthToken, GoogleChallenge
from app.security import current_user, digest, issue, token_row

router = APIRouter(prefix="/auth", tags=["Auth"])

class EmailInput(BaseModel):
    email: str = Field(max_length=254)
    @field_validator("email")
    @classmethod
    def normalize(cls, value):
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address.")
        return value

class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=256)

    @field_validator("email")
    @classmethod
    def normalize(cls, value):
        value = value.strip().lower()
        if not value:
            raise ValueError("Enter your email or username.")
        return value

class RegisterRequest(EmailInput):
    password: str = Field(max_length=256)
    name: str = Field(min_length=1, max_length=80)
    username: Optional[str] = Field(default=None, max_length=30)
    accepted_terms: bool = False

class ResetRequest(BaseModel):
    token: str = Field(min_length=20, max_length=256)
    password: str = Field(max_length=256)

class GoogleRequest(BaseModel):
    credential: str = Field(max_length=8192)
    nonce: str = Field(max_length=256)
    accepted_terms: bool = True

_attempts = {}
def throttle(key, maximum=10):
    now = datetime.now(timezone.utc)
    if len(_attempts) > 10000:
        _attempts.clear()
    recent = [t for t in _attempts.get(key, []) if now-t < timedelta(minutes=15)]
    if len(recent) >= maximum:
        raise HTTPException(429, "Too many attempts. Try again in 15 minutes.")
    _attempts[key] = recent + [now]

def check_password(password):
    if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        raise HTTPException(400, "Use at least 8 characters, including a letter and a number.")
    if len(password.encode()) > 72:
        raise HTTPException(400, "Password must be at most 72 UTF-8 bytes.")

def hash_password(password):
    check_password(password)
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def user_to_dict(user):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}

def signed_in(db, user):
    return {"user": user_to_dict(user), "access_token": issue(db, user.id), "token_type": "bearer"}

@router.post("/register")
def register(data: RegisterRequest, request: Request, db: Session = Depends(get_session)):
    throttle(("register", request.client.host))
    if not data.accepted_terms:
        raise HTTPException(400, "Please accept the terms of use.")
    name = data.name.strip()
    if not name:
        raise HTTPException(400, "Please enter your name.")
    if db.exec(select(User).where(User.email == data.email)).first():
        raise HTTPException(400, "This email is already registered. Please log in.")
    # Chuyển username rỗng (hoặc chỉ toàn khoảng trắng) về None để tránh vi phạm ràng buộc UNIQUE trong DB
    username = (data.username.strip().lower() or None) if getattr(data, "username", None) else None
    if username and db.exec(select(User).where(User.username == username)).first():
        raise HTTPException(400, "This username is already taken.")
    user = User(id=str(uuid.uuid4()), name=name, username=username, email=data.email, password_hash=hash_password(data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "This email is already registered.")
    return signed_in(db, user)

@router.post("/login")
def login(data: LoginRequest, request: Request, db: Session = Depends(get_session)):
    throttle(("login-ip", request.client.host), 100)
    throttle(("login", request.client.host, data.email))
    user = db.exec(select(User).where((User.email == data.email) | (User.username == data.email))).first()
    # Always perform bcrypt work, including when the email does not exist.
    stored = user.password_hash if user and user.password_hash else _dummy
    try:
        ok = bcrypt.checkpw(data.password.encode(), stored.encode())
    except ValueError:
        ok = False
    if not ok or not user or not user.password_hash:
        raise HTTPException(401, "Wrong email or password.")
    return signed_in(db, user)

_dummy = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt()).decode()

@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"user": user_to_dict(user)}

@router.post("/logout")
def logout(request: Request, user: User = Depends(current_user), db: Session = Depends(get_session)):
    raw = request.headers["authorization"].split(" ", 1)[1]
    db.delete(token_row(db, raw))
    db.commit()
    return {"message": "Logged out."}

@router.get("/config")
def config():
    return {"google_client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "password_reset_available": bool(os.getenv("SMTP_HOST"))}

@router.get("/google/nonce")
def google_nonce(request: Request, db: Session = Depends(get_session)):
    throttle(("nonce", request.client.host), 40)
    # No user FK is needed: challenges live in a separate table.
    raw = secrets.token_urlsafe(32)
    db.add(GoogleChallenge(digest=digest(raw), expires_at=datetime.now(timezone.utc)+timedelta(minutes=5)))
    db.commit()
    return {"nonce": raw}

@router.post("/google")
def google_login(data: GoogleRequest, request: Request, db: Session = Depends(get_session)):
    throttle(("google", request.client.host), 20)
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    if not client_id:
        raise HTTPException(503, "Google sign-in is not configured.")
    challenge = db.get(GoogleChallenge, digest(data.nonce))
    if not challenge or challenge.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(401, "Google challenge expired. Refresh the page.")
    try:
        from google.oauth2 import id_token
        from google.auth.transport.requests import Request as GoogleTransport
        info = id_token.verify_oauth2_token(data.credential, GoogleTransport(), client_id)
        if info.get("nonce") != data.nonce or not info.get("email_verified") or not info.get("sub"):
            raise ValueError("Invalid identity")
    except Exception:
        raise HTTPException(401, "Google identity could not be verified. Please try again.")
    consumed = db.exec(delete(GoogleChallenge).where(GoogleChallenge.digest == challenge.digest))
    if consumed.rowcount != 1:
        db.rollback()
        raise HTTPException(401, "Google challenge has already been used. Refresh the page.")
    db.commit()
    user = db.exec(select(User).where(User.google_sub == info["sub"])).first()
    if not user:
        email = info["email"].strip().lower()
        if db.exec(select(User).where(User.email == email)).first():
            raise HTTPException(409, "This email already has an account. Log in with your password or reset it.")
        if not data.accepted_terms:
            raise HTTPException(400, "Accept the terms before creating a Google account.")
        user = User(id=str(uuid.uuid4()), name=info.get("name", "Learner")[:80], email=email,
                    password_hash="", google_sub=info["sub"])
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Account already exists. Please log in again.")
    return signed_in(db, user)

@router.post("/forgot-password")
def forgot(data: EmailInput, request: Request, db: Session = Depends(get_session)):
    throttle(("reset-ip", request.client.host), 10)
    throttle(("reset-email", data.email), 3)
    if not os.getenv("SMTP_HOST"):
        raise HTTPException(503, "Password recovery email is not configured. Contact the project administrator.")
    user = db.exec(select(User).where((User.email == data.email) | (User.username == data.email))).first()
    if user:
        raw = issue(db, user.id, "reset", 15)
        link = os.getenv("FRONTEND_URL", "http://localhost:5500").rstrip("/") + "/?" + urlencode({"reset_token": raw})
        message = EmailMessage()
        message["Subject"] = "Reset your StoryLingo password"
        message["From"] = os.getenv("SMTP_FROM") or os.getenv("SMTP_USER") or "storylingo@localhost"
        message["To"] = user.email
        message.set_content(f"Use this link within 15 minutes: {link}\nIf you did not request this, ignore this email.")
        try:
            with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.getenv("SMTP_PORT", "587")), timeout=15) as smtp:
                if os.getenv("SMTP_STARTTLS", "true").lower() == "true":
                    smtp.starttls(context=ssl.create_default_context())
                if os.getenv("SMTP_USER"):
                    smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
                smtp.send_message(message)
        except Exception:
            logging.getLogger(__name__).error("Password recovery delivery failed")
            db.delete(db.get(AuthToken, digest(raw)))
            db.commit()
    return {"message": "If this email is registered, a reset link will be sent. Check your inbox and spam folder."}

@router.post("/reset-password")
def reset(data: ResetRequest, db: Session = Depends(get_session)):
    row = token_row(db, data.token, "reset")
    hashed = hash_password(data.password)
    # Atomic consumption prevents reuse even with concurrent requests.
    used = db.exec(delete(AuthToken).where(AuthToken.digest == row.digest))
    if used.rowcount != 1:
        db.rollback()
        raise HTTPException(401, "This reset link has already been used.")
    user = db.get(User, row.user_id)
    user.password_hash = hashed
    for other in db.exec(select(AuthToken).where(AuthToken.user_id == user.id)).all():
        db.delete(other)
    db.add(user)
    db.commit()
    return {"message": "Password updated. Please log in again."}
