from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_session

# Import các bảng dữ liệu cần để làm thống kê
from app.models import Story, UserVocabulary, QuizResult, Vocabulary

router = APIRouter(prefix="/dashboard", tags=["Bảng Điều Khiển (Dashboard)"])

@router.get("/{user_id}")
def get_dashboard_data(user_id: str, db: Session = Depends(get_session)):
    """
    API này gom toàn bộ số liệu của 1 user để hiển thị lên trang Dashboard.
    Viết theo phong cách "đếm từng thứ một" rất dễ hiểu.
    """
    
    # 1. Đếm số truyện user đã tạo
    # Lấy tất cả truyện của user này rồi dùng hàm len() để đếm
    stories = db.execute(select(Story).where(Story.user_id == user_id)).scalars().all()
    total_stories = len(stories)

    # 2. Đếm số từ vựng đang học trong sổ tay
    vocab_list = db.execute(select(UserVocabulary).where(UserVocabulary.user_id == user_id)).scalars().all()
    words_learned = len(vocab_list)

    # 3. Tính tỷ lệ làm Quiz chính xác (Accuracy %)
    quizzes = db.execute(select(QuizResult).where(QuizResult.user_id == user_id)).scalars().all()
    total_quizzes = len(quizzes)
    
    # Đếm xem có bao nhiêu câu user chọn đúng (is_correct == True)
    correct_quizzes = sum(1 for q in quizzes if q.is_correct)
    
    accuracy = 0.0
    if total_quizzes > 0:
        # Công thức: (số câu đúng / tổng số câu) * 100, làm tròn 1 chữ số
        accuracy = round((correct_quizzes / total_quizzes) * 100, 1)

    # 4. Lấy 5 từ vựng vừa ôn tập gần đây nhất (để hiển thị bảng "Recent Words")
    # Gộp bảng Vocabulary (lấy chữ) và UserVocabulary (lấy điểm)
    statement = (
        select(Vocabulary.word, UserVocabulary.mastery_level)
        .join(UserVocabulary, Vocabulary.id == UserVocabulary.vocabulary_id)
        .where(UserVocabulary.user_id == user_id)
        .order_by(UserVocabulary.id.desc()) # Sắp xếp mới nhất lên đầu
        .limit(5)                           # Chỉ lấy 5 từ
    )
    recent_words_db = db.execute(statement).all()
    
    # Gói dữ liệu 5 từ vựng vào một mảng
    recent_words = []
    for word, mastery in recent_words_db:
        recent_words.append({
            "word": word,
            "mastery_level": mastery
        })

    # 5. Gói toàn bộ dữ liệu trả về cho Frontend
    return {
        "message": "Lấy dữ liệu thống kê thành công!",
        "statistics": {
            "total_stories": total_stories,
            "words_learned": words_learned,
            "quiz_accuracy": f"{accuracy}%"
        },
        "recent_words": recent_words
    }