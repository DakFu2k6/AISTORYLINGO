import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext

from app.database import get_session
from app.models import User, UserPreference

router = APIRouter(prefix="/auth", tags=["Xác Thực & Người Dùng"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 1. API ĐĂNG KÝ (TẠO TÀI KHOẢN MỚI)

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

@router.post("/register")
def register_user(data: RegisterRequest, db: Session = Depends(get_session)):
    """
    Nhận thông tin tạo tài khoản từ giao diện. 
    Mã hóa mật khẩu bằng bcrypt trước khi lưu xuống Database.
    """
    # Bước 1: Kiểm tra xem email đã được đăng ký chưa
    statement = select(User).where(User.email == data.email)
    existing_user = db.execute(statement).scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email này đã được sử dụng. Vui lòng đăng nhập!"
        )

    # Bước 2: Băm mật khẩu (Mã hóa)
    hashed_password = pwd_context.hash(data.password)

    # Bước 3: Tạo ID tự động và lưu thông tin
    new_user = User(
        id=str(uuid.uuid4()),  # Tạo chuỗi ID độc nhất
        email=data.email,
        name=data.name,
        password_hash=hashed_password # Lưu mật khẩu đã mã hóa
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Tạo tài khoản thành công", "user_id": new_user.id}


# 2. API ĐĂNG NHẬP BẰNG EMAIL & PASSWORD
class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
def login_user(data: LoginRequest, db: Session = Depends(get_session)):
    """
    Kiểm tra email và giải mã mật khẩu xem có khớp với Database hay không.
    """
    # Bước 1: Tìm user theo email
    statement = select(User).where(User.email == data.email)
    user = db.execute(statement).scalars().first()

    # Bước 2: Đối chiếu mật khẩu người dùng nhập với mật khẩu băm trong DB
    if not user or not user.password_hash or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác!"
        )

    # Bước 3: Trả về thông tin nếu đăng nhập đúng
    return {
        "message": "Đăng nhập thành công!",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }

# 3. API LƯU THÔNG TIN KHẢO SÁT (ONBOARDING)
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
    Lưu lại các lựa chọn của User (Ví dụ: Học tiếng Anh, Level B1, Thích Mystery...)
    """
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