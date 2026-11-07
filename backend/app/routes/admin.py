from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlmodel import Session, select
from app.database import get_session
from app.models import User, Story, QuizResult, Vocabulary
from app.security import admin_user
from app.routes.auth import user_to_dict

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(admin_user)])

@router.get("/overview")
def overview(db: Session = Depends(get_session)):
    return {name: db.exec(select(func.count()).select_from(model)).one()
            for name, model in [("users", User), ("stories", Story), ("answers", QuizResult), ("words", Vocabulary)]}

@router.get("/users")
def users(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50), db: Session = Depends(get_session)):
    total = db.exec(select(func.count()).select_from(User)).one()
    rows = db.exec(select(User).order_by(User.created_at.desc(), User.id).offset((page-1)*page_size).limit(page_size)).all()
    return {"data": [user_to_dict(u) for u in rows], "total": total, "page": page, "page_size": page_size}
