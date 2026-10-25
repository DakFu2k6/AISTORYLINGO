import uuid
import bcrypt

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

def user_to_dict(user: User) -> dict:
    return {"id": user.id, "name": user.name, "email": user.email}

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_session)):
    name = data.name.strip()
    email = data.email.strip().lower()

    if not name:
        raise HTTPException(400, "Please enter your name.")
    if "@" not in email:
        raise HTTPException(400, "Please enter a valid email.")
    if len(data.password) < 6:
        raise HTTPException(400, "Password must have at least 6 characters.")
    if len(data.password.encode("utf-8")) > 72:
        raise HTTPException(400, "Password is too long (max 72 bytes).")
    if db.exec(select(User).where(User.email == email)).first():
        raise HTTPException(400, "This email is already registered. Please log in.")

    hashed = bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(id=str(uuid.uuid4()), name=name, email=email, password_hash=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Account created!", "user": user_to_dict(user)}


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_session)):
    email = data.email.strip().lower()
    user = db.exec(select(User).where(User.email == email)).first()

    try:
        ok = bool(user) and bcrypt.checkpw(
            data.password.encode("utf-8"), user.password_hash.encode("utf-8")
        )
    except ValueError:
        ok = False
    if not ok:
        raise HTTPException(401, "Wrong email or password.")

    return {"message": "Logged in!", "user": user_to_dict(user)}
