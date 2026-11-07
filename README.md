# AI StoryLingo — Web MidTerm

Ứng dụng học ngoại ngữ qua truyện tương tác: tạo truyện, chọn diễn biến, lưu từ, luyện quiz và theo dõi tiến bộ. Frontend HTML/CSS/JavaScript; backend FastAPI + SQLModel; SQLite mặc định, hỗ trợ PostgreSQL; Gemini tùy chọn.

**Đọc [hướng dẫn nâng cấp chi tiết](docs/UPGRADE_GUIDE_VI.md) trước khi ghép vào bài nhóm.** Toàn bộ file trong gói là code hoàn chỉnh, không phải đoạn code cần tự chèn.

## Chạy trên Windows / PowerShell

Cần Python 3.10 trở lên. Giải nén, mở terminal tại thư mục `AiStoryLingo`.

```powershell
Copy-Item .env.example .env
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal thứ hai, từ `AiStoryLingo`:

```powershell
cd frontend
python -m http.server 5500
```

Mở **http://localhost:5500**. API: **http://localhost:8000/docs**. Không mở HTML bằng `file://`. Không cần kích hoạt venv nên tránh được lỗi PowerShell execution policy.

Mặc định không cần API key: ứng dụng dùng truyện demo và hiển thị nhãn Demo. Điền `GEMINI_API_KEY` vào `.env` ở thư mục gốc để dùng AI thật. `.env` ở gốc được đọc trước, `backend/.env` chỉ bổ sung biến chưa có; biến môi trường hệ điều hành ưu tiên cao nhất. Khởi động lại backend sau khi đổi cấu hình.

## Tính năng mới

- Giao diện sáng, bố cục responsive; menu hamburger dưới 760px.
- Đăng nhập email, kiểm tra email/password, mật khẩu bcrypt, giới hạn thử đăng nhập.
- Phiên Bearer ngẫu nhiên có hạn 24 giờ, lưu hash ở database, thu hồi khi logout/reset.
- Google Identity Services với kiểm tra chữ ký, audience, hạn token và nonce ở backend.
- Quên mật khẩu qua SMTP, liên kết 15 phút dùng một lần, xác nhận mật khẩu mới.
- Admin dashboard: thống kê và danh sách người dùng có phân trang; backend kiểm tra role.
- Điều khoản và thông báo quyền riêng tư; đăng ký mới phải đồng ý.
- Phân trang tại My words, My stories (6 mục/trang), Admin users (10 mục/trang).

## Cấp quyền admin

Đăng ký tài khoản thường bằng giao diện, rồi mở terminal thứ ba tại `backend`:

```powershell
.\.venv\Scripts\python.exe manage_admin.py your-email@example.com
```

Đăng nhập lại để thấy mục Admin. Không có tài khoản admin/mật khẩu mặc định và không có API công khai tự cấp quyền.

## Google và quên mật khẩu

Điền `GOOGLE_CLIENT_ID` để bật Google Sign-In. Đăng ký OAuth Web application, thêm JavaScript origin `http://localhost:5500`. Đây là luồng ID token JavaScript callback, không dùng client secret trong frontend. Xem hướng dẫn chi tiết trong `docs/UPGRADE_GUIDE_VI.md`.

Điền `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` và `FRONTEND_URL=http://localhost:5500` để bật gửi email reset. Không có SMTP thì giao diện hiển thị lỗi cấu hình rõ ràng; không trả reset token cho trình duyệt.

## Kiểm thử

Từ thư mục `backend`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Test dùng SQLite tạm và AI giả lập/demo, không sửa database thật, không gọi Google hoặc gửi email thật. Chi tiết phạm vi kiểm thử và giới hạn ở hướng dẫn nâng cấp.

## Dữ liệu cũ

Sao lưu database trước khi cập nhật. Với SQLite, sao chép `backend/storylingo.db` từ bản cũ sang thư mục backend của bản mới khi server đã dừng. Server tự bổ sung các cột cần thiết; không cần xóa tài khoản cũ. Mật khẩu cũ vẫn đăng nhập được; quy tắc 8 ký tự áp dụng cho đăng ký/reset mới. Các phiên ở bản cũ không còn giá trị, cần đăng nhập lại.

Gói bàn giao chỉ chứa source và `.env.example`, không chứa `.env` riêng, database cá nhân, `.git`, venv hoặc cache. Giữ lại cấu hình và dữ liệu gốc của nhóm riêng để ghép lại.
