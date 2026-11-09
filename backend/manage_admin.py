import sys
from sqlmodel import Session, select
from app.database import engine, create_db_and_tables
from app.models import User

# Script cấp quyền Quản trị viên (Admin) cho tài khoản đã đăng ký trong hệ thống
if __name__ == "__main__":
    create_db_and_tables()

    # Kiểm tra tham số dòng lệnh: bắt buộc phải truyền email của tài khoản
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        print("=" * 60)
        print("📌 HƯỚNG DẪN CẤP QUYỀN ADMIN (USAGE)")
        print("=" * 60)
        print("Cú pháp: python manage_admin.py <email_tai_khoan>")
        print("Ví dụ  : python manage_admin.py admin@example.com")
        print("\nLưu ý  : Tài khoản cần được đăng ký trước trên trang Web.")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    with Session(engine) as db:
        user = db.exec(select(User).where(User.email == email)).first()
        if not user:
            print(f"❌ Không tìm thấy người dùng với email: '{email}'")
            print("👉 Vui lòng mở trang web đăng ký tài khoản trước, sau đó chạy lại lệnh này.")
            sys.exit(1)

        # Nâng cấp vai trò thành admin
        user.role = "admin"
        db.add(user)
        db.commit()
        print(f"✅ Đã cấp quyền Quản trị viên (Admin) thành công cho tài khoản: {email}")
        print("👉 Vui lòng đăng xuất và đăng nhập lại trên web để truy cập trang Admin Dashboard.")
