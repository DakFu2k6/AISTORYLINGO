from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select
from app.database import get_session
from app.models import Vocabulary, UserVocabulary

# Khởi tạo router
router = APIRouter(prefix="/vocabulary", tags=["Hệ Thống Học Từ Vựng"])

# 1. Form dữ liệu khi Frontend gửi yêu cầu lưu từ vựng
class SaveVocabRequest(BaseModel):
    user_id: str
    vocabulary_id: int

# 2. API Lưu từ vựng vào sổ tay
@router.post("/save")
def save_vocabulary(request: SaveVocabRequest, db: Session = Depends(get_session)):
    statement = select(UserVocabulary).where(
        UserVocabulary.user_id == request.user_id,
        UserVocabulary.vocabulary_id == request.vocabulary_id
    )
    existing_word = db.exec(statement).first()

    if existing_word:
        existing_word.times_reviewed += 1
        db.commit()
        return {"message": "Đã ôn lại từ vựng!", "data": existing_word}

    new_user_vocab = UserVocabulary(
        user_id=request.user_id,
        vocabulary_id=request.vocabulary_id,
        times_reviewed=1,
        mastery_level=0,
        correct_answers=0
    )
    db.add(new_user_vocab)
    db.commit()
    db.refresh(new_user_vocab)
    
    return {"message": "Đã thêm từ vựng mới vào sổ tay!", "data": new_user_vocab}

# 3. API Lấy danh sách sổ tay từ vựng của một user
@router.get("/user/{user_id}")
def get_user_vocabulary(user_id: str, db: Session = Depends(get_session)):
    statement = select(Vocabulary, UserVocabulary).join(
        UserVocabulary, Vocabulary.id == UserVocabulary.vocabulary_id
    ).where(UserVocabulary.user_id == user_id)
    
    # Lấy dữ liệu bằng SQLModel
    results = db.exec(statement).all()
    
    vocab_list = []
    for vocab, user_vocab in results:
        vocab_list.append({
            "word": vocab.word,
            "meaning": vocab.meaning,
            "example": vocab.example,
            "times_reviewed": user_vocab.times_reviewed,
            "mastery_level": user_vocab.mastery_level
        })
        
    # Đã đổi key "vocabularies" thành "data" để khớp 100% với Frontend của Member 1
    return {
        "message": "Lấy danh sách từ vựng thành công!", 
        "total_words": len(vocab_list),
        "data": vocab_list
    }