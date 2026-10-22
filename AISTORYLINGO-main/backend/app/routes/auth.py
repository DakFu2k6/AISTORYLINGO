import uuid
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Import các công cụ cơ sở dữ liệu
from app.database import get_session
from app.models import User, UserPreference

# Tạo router
router = APIRouter(prefix="/auth", tags=["Xác Thực & Người Dùng"])


# 1. API ĐĂNG KÝ (Băm mật khẩu bằng Bcrypt thuần)
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

@router.post("/register")
def register_user(data: RegisterRequest, db: Session = Depends(get_session)):
    """
    Đăng ký tài khoản mới: Băm mật khẩu bằng bcrypt và lưu xuống Supabase.
    """
    # 1. Kiểm tra xem email đã tồn tại chưa
    statement = select(User).where(User.email == data.email)
    existing_user = db.execute(statement).scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email này đã được sử dụng. Vui lòng đăng nhập!"
        )

    # 2. Băm mật khẩu bằng bcrypt trực tiếp
    password_bytes = data.password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    # 3. Tạo user mới và lưu vào cơ sở dữ liệu
    new_user = User(
        id=str(uuid.uuid4()),
        email=data.email,
        name=data.name,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Tạo tài khoản thành công", "user_id": new_user.id}


# 2. API ĐĂNG NHẬP (Xác thực mật khẩu)
class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
def login_user(data: LoginRequest, db: Session = Depends(get_session)):
    """
    Đăng nhập: Kiểm tra mật khẩu mã hóa trong Database bằng bcrypt.checkpw.
    """
    statement = select(User).where(User.email == data.email)
    user = db.execute(statement).scalars().first()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác!"
        )

    # Đối chiếu mật khẩu bằng bcrypt.checkpw
    input_pwd_bytes = data.password.encode('utf-8')
    stored_hash_bytes = user.password_hash.encode('utf-8')

    if not bcrypt.checkpw(input_pwd_bytes, stored_hash_bytes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác!"
        )

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

# 4. API ĐĂNG NHẬP MẠNG XÃ HỘI (Google / Facebook)
class SocialLoginRequest(BaseModel):
    provider: str
    email: str
    name: str

@router.post("/social-login")
def social_login(data: SocialLoginRequest, db: Session = Depends(get_session)):
    """
    API giả lập đăng nhập bằng Google/Facebook cho đồ án.
    Tự động kiểm tra và tạo user nếu chưa tồn tại trong Database.
    """
    # Kiểm tra xem email này đã có trong Database chưa
    statement = select(User).where(User.email == data.email)
    user = db.execute(statement).scalars().first()

    # Nếu chưa có thì tạo mới ngay lập tức (không cần mật khẩu)
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email=data.email,
            name=data.name,
            password_hash=f"SOCIAL_LOGIN_{data.provider.upper()}" # Đánh dấu nguồn gốc
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return {
        "message": f"Đăng nhập bằng {data.provider.capitalize()} thành công!",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }