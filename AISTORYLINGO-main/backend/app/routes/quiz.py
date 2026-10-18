from fastapi import APIRouter, Depends
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_session
from app.models import Quiz, QuizResult, UserVocabulary

router = APIRouter(prefix="/quiz", tags=["Hệ Thống Trò Chơi & Bài Tập"])

# 1. Định nghĩa dữ liệu Frontend gửi lên khi user nộp bài
class SubmitQuizRequest(BaseModel):
    user_id: str
    quiz_id: int
    answer: str          # Đáp án user chọn (ví dụ: "A")
    vocabulary_id: int   # ID của từ vựng đang được kiểm tra

# 2. API Chấm điểm và Cập nhật tiến độ
@router.post("/submit")
def submit_quiz(request: SubmitQuizRequest, db: Session = Depends(get_session)):
    """
    API này làm 3 việc:
    1. Kiểm tra xem user chọn đúng hay sai.
    2. Lưu lịch sử làm bài vào bảng 'quiz_results'.
    3. Nếu đúng, tăng độ thông thạo (mastery_level) của từ vựng đó lên.
    """
    # Lấy câu hỏi từ Database để đối chiếu đáp án
    quiz_obj = db.get(Quiz, request.quiz_id)
    if not quiz_obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi này trong cơ sở dữ liệu!")

    # So sánh đáp án của user với đáp án chuẩn
    is_correct = (request.answer.strip().upper() == quiz_obj.correct_answer.strip().upper())

    # Lưu lịch sử nộp bài
    new_result = QuizResult(
        user_id=request.user_id,
        quiz_id=request.quiz_id,
        answer=request.answer,
        is_correct=is_correct
    )
    db.add(new_result)

    # Cập nhật độ thông thạo (Mastery Level) cho từ vựng
    statement = select(UserVocabulary).where(
        UserVocabulary.user_id == request.user_id,
        UserVocabulary.vocabulary_id == request.vocabulary_id
    )
    user_vocab = db.execute(statement).scalars().first()

    if user_vocab:
        # Nếu user trả lời đúng, cộng 20% độ thông thạo và ghi nhận 1 lần đúng
        if is_correct:
            user_vocab.correct_answers += 1
            user_vocab.mastery_level = min(100, user_vocab.mastery_level + 20) # Tối đa là 100%
        # Nếu trả lời sai, trừ nhẹ 10% để user phải ôn lại
        else:
            user_vocab.mastery_level = max(0, user_vocab.mastery_level - 10) # Không rớt xuống dưới 0%
            
        db.add(user_vocab)

    db.commit()

    return {
        "message": "Nộp bài thành công!",
        "is_correct": is_correct,
        "correct_answer": quiz_obj.correct_answer if not is_correct else None,
        "new_mastery_level": user_vocab.mastery_level if user_vocab else 0
    }