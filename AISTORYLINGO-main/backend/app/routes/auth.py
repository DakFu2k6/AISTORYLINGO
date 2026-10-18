from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Import các công cụ mình đã làm ở Tuần 1
from app.database import get_session
from app.models import User, UserPreference

# Tạo router (giống như gom nhóm các API có chung chữ "/auth" ở đầu)
router = APIRouter(prefix="/auth", tags=["Xác Thực & Người Dùng"])

# ---------------------------------------------------------
# 1. API ĐĂNG NHẬP LƯU USER VÀO DATABASE
# ---------------------------------------------------------

# Định nghĩa cái form dữ liệu mà Frontend sẽ gửi lên
class LoginRequest(BaseModel):
    uid: str      # Cấu trúc y hệt UID của Firebase
    email: str
    name: str

@router.post("/login")
def login_user(data: LoginRequest, db: Session = Depends(get_session)):
    """
    API này nhận dữ liệu từ Frontend sau khi user đăng nhập Firebase thành công.
    Nếu user chưa có trong database -> Tạo mới.
    Nếu user có rồi -> Trả về thông tin user đó.
    """
    # Bước 1: Tìm xem uid này đã có trong bảng users chưa
    statement = select(User).where(User.id == data.uid)
    existing_user = db.execute(statement).scalars().first()

    # Bước 2: Nếu chưa có (người dùng mới)
    if not existing_user:
        new_user = User(
            id=data.uid,
            email=data.email,
            name=data.name
        )
        db.add(new_user)
        db.commit()      # Lưu vào database
        db.refresh(new_user)
        return {"message": "Tạo người dùng mới thành công", "user": new_user}
    
    # Bước 3: Nếu có rồi (người dùng cũ đăng nhập lại)
    return {"message": "Chào mừng bạn quay lại", "user": existing_user}

# ---------------------------------------------------------
# 2. API LƯU THÔNG TIN KHẢO SÁT (ONBOARDING)
# ---------------------------------------------------------

# Form dữ liệu sở thích học tập Frontend gửi lên
class PreferenceRequest(BaseModel):
    user_id: str
    language: str
    level: str
    interests: str
    learning_goals: str
    target_vocabulary: int

@router.post("/preferences")
def save_preferences(data: PreferenceRequest, db: Session = Depends(get_session)):
    """
    API này dùng để lưu lại các lựa chọn của User (Ví dụ: Học tiếng Anh, Level B1, Thích Mystery...)
    """
    # Tạo một bản ghi mới trong bảng user_preferences
    new_pref = UserPreference(
        user_id=data.user_id,
        language=data.language,
        level=data.level,
        interests=data.interests,
        learning_goals=data.learning_goals,
        target_vocabulary=data.target_vocabulary
    )
    
    db.add(new_pref)
    db.commit()
    db.refresh(new_pref)
    
    return {"message": "Đã lưu hồ sơ học tập thành công!", "preferences": new_pref}