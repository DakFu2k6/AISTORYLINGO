# Vận hành, cấu hình và xử lý sự cố

## Khởi động và health

Backend chạy từ thư mục `backend` bằng `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`. Frontend chạy từ `frontend` bằng `python -m http.server 5500`. `--reload` chỉ dùng phát triển, không dùng production.

Kiểm tra theo thứ tự: `http://127.0.0.1:8000/health` → `http://127.0.0.1:8000/docs` → `http://localhost:5500` → đăng nhập → tạo truyện demo → quiz.

## Cấu hình `.env`

| Nhóm | Biến |
|---|---|
| AI | `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_BACKEND`, `GEMINI_TIMEOUT_SECONDS` |
| Giới hạn | `GENERATE_LIMIT_PER_HOUR` |
| Database | `DATABASE_URL` |
| Web | `CORS_ORIGINS`, `FRONTEND_URL` |
| Google | `GOOGLE_CLIENT_ID` |
| Email | `SMTP_HOST`, `SMTP_PORT`, `SMTP_STARTTLS`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` |

`.env` gốc được nạp trước, `backend/.env` bổ sung giá trị chưa tồn tại; biến môi trường hệ điều hành có ưu tiên cao hơn. Sau thay đổi, restart backend.

## Lỗi phổ biến

**Backend import error:** kiểm tra Python của `.venv`, cài `requirements.txt`, chạy đúng từ thư mục `backend`. **Port occupied:** đóng process chiếm port; nếu đổi port backend phải cập nhật URL API frontend, nếu đổi port frontend phải cập nhật CORS, Google OAuth origin và `FRONTEND_URL`. **Google lỗi:** xem `/auth/config`, origin, client ID, nonce, HTTPS/domain production. **SMTP lỗi:** kiểm tra STARTTLS/port/app password, không in mật khẩu ra log. **Gemini demo:** xem `/health/ai`, quota, model, key; fallback là hành vi dự kiến.

## Dữ liệu và backup

Dừng backend trước khi copy SQLite `backend/storylingo.db`. Với PostgreSQL, lên lịch `pg_dump` và thử phục hồi. Không copy `.env` hay DB vào artifact công khai. `SQLModel.create_all()` không xử lý migration phá vỡ schema; lập migration và backup trước khi thay đổi model.

## Triển khai production — chỉ là định hướng

Frontend cần được host qua HTTPS; backend đặt sau reverse proxy HTTPS, CORS hạn chế theo origin, cấu hình secrets ngoài source, DB managed có backup, migration, logging/monitoring và rate limit tập trung. Chưa có Dockerfile/CI/CD trong bản nguồn được rà soát; không mô tả production deployment là đã hoàn thiện.
