# Hướng dẫn cài đặt đầy đủ

## 1. Chuẩn bị

Cài Python 3.10+ (khuyến nghị 3.11/3.12), đảm bảo `py -3 --version` (Windows) hoặc `python3 --version` (macOS/Linux) hoạt động. Giải nén project, mở terminal ở thư mục `AiStoryLingo`. Kiểm tra có `backend/requirements.txt`, `frontend/index.html`, `.env.example`.

## 2. Windows PowerShell

**Terminal A — backend:**

```powershell
Copy-Item .env.example .env
cd backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal B — frontend:** mở PowerShell mới tại `AiStoryLingo`:

```powershell
cd frontend
py -3 -m http.server 5500 --bind 127.0.0.1
```

**Truy cập:** `http://localhost:5500` và `http://127.0.0.1:8000/docs`. Không cần `Activate.ps1`; cách gọi Python trực tiếp tránh lỗi execution policy.

## 3. macOS / Linux

```bash
cp .env.example .env
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal thứ hai, từ thư mục `AiStoryLingo`:

```bash
cd frontend
python3 -m http.server 5500 --bind 127.0.0.1
```

## 4. Chạy lần đầu

1. Kiểm tra `/health` trả status ok.
2. Vào frontend, đăng ký email, username, mật khẩu ít nhất 8 ký tự có chữ và số, đồng ý điều khoản.
3. Đăng nhập, tạo truyện. Khi `GEMINI_API_KEY` trống, service tự dùng demo.
4. Chọn hướng đi, lưu từ và làm quiz, sau đó xem dashboard.
5. Dừng hai terminal bằng `Ctrl+C`; SQLite được lưu ở `backend/storylingo.db`.

## 5. Kích hoạt Gemini

Điền `GEMINI_API_KEY` vào `.env` gốc. Mặc định `GEMINI_MODEL=gemini-2.5-flash`, `GEMINI_BACKEND=auto`; key bắt đầu `AQ.` được định tuyến Vertex Express, key khác dùng AI Studio. Khởi động lại backend; xem `/health/ai`. Chỉ dùng `?probe=true` khi chủ động thử gọi API vì có thể tính quota.

## 6. Google Sign-In

Trong Google Cloud Console, tạo OAuth Client ID loại **Web application**, cấu hình Authorized JavaScript origins: `http://localhost:5500` (thêm `http://127.0.0.1:5500` nếu thực sự truy cập bằng host này). Đặt `GOOGLE_CLIENT_ID=<web-client-id>` trong `.env`, restart backend, reload frontend. Không đặt Google client secret vào frontend. Chức năng phụ thuộc chính sách và cấu hình OAuth của Google; có thể cần thêm tài khoản test vào OAuth consent screen.

## 7. Quên mật khẩu qua SMTP

Cấu hình `SMTP_HOST`, `SMTP_PORT`, `SMTP_STARTTLS`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `FRONTEND_URL=http://localhost:5500`. Dùng credential SMTP/app password riêng của nhà cung cấp, không dùng mật khẩu tài khoản chính nếu nhà cung cấp yêu cầu app password. Restart backend; thử yêu cầu reset với email đã đăng ký và kiểm tra inbox/spam. Reset token có hiệu lực 15 phút, một lần.

## 8. PostgreSQL tùy chọn

Tạo database và user trên PostgreSQL trước. Đặt `DATABASE_URL=postgresql://app_user:YOUR_PASSWORD@127.0.0.1:5432/storylingo` trong `.env`; thay thông tin bằng credential thực. Package `psycopg2-binary` có trong requirements. Khởi động backend để SQLModel tạo bảng; trước khi chuyển từ SQLite sang PostgreSQL cần migration dữ liệu riêng, **không tự động chuyển dữ liệu cũ**.

## 9. Admin

Đăng ký user thường trước, tại terminal `backend` chạy:

```powershell
.\.venv\Scripts\python.exe manage_admin.py user@example.com
```

Sau đó đăng xuất/đăng nhập lại. Script không tạo admin mới; nó nâng role của tài khoản đã có.

## 10. Chạy kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

## 11. Lưu ý khi bàn giao

Không đính kèm `.env` có secret, `storylingo.db` chứa dữ liệu thật, `.git`, `.venv`, cache. Chỉ cung cấp `.env.example`. Sao lưu DB trước khi cập nhật. Xem `OPERATIONS.md` khi lỗi và `CODE_REVIEW.md` về giới hạn kỹ thuật.
