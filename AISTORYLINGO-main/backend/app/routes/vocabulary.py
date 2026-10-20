from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_session
# Import bảng Vocabulary (thông tin từ vựng) và UserVocabulary (sổ tay cá nhân)
from app.models import Vocabulary, UserVocabulary
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db 
from app.models import Story

router = APIRouter(prefix="/vocabulary", tags=["Hệ Thống Học Từ Vựng"])

# 1. Form dữ liệu khi Frontend gửi yêu cầu lưu từ vựng
class SaveVocabRequest(BaseModel):
    user_id: str
    vocabulary_id: int

# 2. API Lưu từ vựng vào sổ tay
@router.post("/save")
def save_vocabulary(request: SaveVocabRequest, db: Session = Depends(get_session)):
    """
    API này chạy khi người dùng bấm "+ Add to vocabulary".
    Nếu từ này chưa có trong sổ tay -> Thêm mới.
    Nếu có rồi -> Tăng số lần ôn tập (times_reviewed) lên 1.
    """
    # Bước 1: Kiểm tra xem user đã lưu từ này vào sổ tay chưa
    statement = select(UserVocabulary).where(
        UserVocabulary.user_id == request.user_id,
        UserVocabulary.vocabulary_id == request.vocabulary_id
    )
    existing_word = db.execute(statement).scalars().first()

    # Bước 2: Nếu đã lưu rồi thì cộng dồn số lần xem (Rất hữu ích để đánh giá mức độ nhớ từ)
    if existing_word:
        existing_word.times_reviewed += 1
        db.commit()
        return {"message": "Đã ôn lại từ vựng!", "data": existing_word}

    # Bước 3: Nếu chưa lưu thì tạo bản ghi mới trong sổ tay
    new_user_vocab = UserVocabulary(
        user_id=request.user_id,
        vocabulary_id=request.vocabulary_id,
        times_reviewed=1,
        mastery_level=0, # Mới lưu nên độ thông thạo bằng 0
        correct_answers=0
    )
    db.add(new_user_vocab)
    db.commit()
    db.refresh(new_user_vocab)
    
    return {"message": "Đã thêm từ vựng mới vào sổ tay!", "data": new_user_vocab}


# 3. API Lấy danh sách sổ tay từ vựng của một user
@router.get("/user/{user_id}")
def get_user_vocabulary(user_id: str, db: Session = Depends(get_session)):
    """
    API này dùng để hiển thị danh sách từ vựng trên trang Dashboard.
    Nó sẽ kết hợp (JOIN) bảng Vocabulary và UserVocabulary lại với nhau.
    """
    # Lấy thông tin từ cả 2 bảng: Từ vựng là gì (Vocabulary) và User đã học tới đâu (UserVocabulary)
    statement = select(Vocabulary, UserVocabulary).join(
        UserVocabulary, Vocabulary.id == UserVocabulary.vocabulary_id
    ).where(UserVocabulary.user_id == user_id)
    
    results = db.execute(statement).all()
    
    vocab_list = []
    for vocab, user_vocab in results:
        vocab_list.append({
            "word": vocab.word,
            "meaning": vocab.meaning,
            "example": vocab.example,
            "times_reviewed": user_vocab.times_reviewed,
            "mastery_level": user_vocab.mastery_level
        })
        
    return {
        "message": "Lấy danh sách từ vựng thành công!", 
        "total_words": len(vocab_list),
        "vocabularies": vocab_list
    }
    
@router.get("/vocabulary/user/{user_id}")
def get_user_vocabulary(user_id: str, db: Session = Depends(get_db)):
    return {"data": []} 

