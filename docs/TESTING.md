# Chiến lược kiểm thử

## Test tự động hiện có

| File | Mục tiêu |
|---|---|
| `backend/tests/test_api_flow.py` | Luồng API học tập |
| `backend/tests/test_security.py` | Kiểm tra auth và bảo vệ truy cập |
| `backend/tests/test_ai_service.py` | Logic AI, schema, fallback |
| `backend/tests/test_progress.py` | XP và tiến độ |
| `backend/tests/conftest.py` | Fixtures, database test |

## Chạy test

Windows (terminal tại `backend`):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -v tests/test_security.py
```

Linux/macOS (terminal tại `backend`):

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

Test dùng SQLite thử nghiệm và không được xem là phép thử tích hợp Google/SMTP/Gemini thật.

## Checklist E2E thủ công

- [ ] `GET /health` trả `{"status":"ok"}`.
- [ ] Frontend tải qua HTTP ở port 5500, không lỗi CORS.
- [ ] Đăng ký mới có xác nhận điều khoản; không đăng ký email trùng.
- [ ] Login email và username, sai mật khẩu bị từ chối.
- [ ] Logout và token cũ không còn truy cập API.
- [ ] Hai user khác nhau không đọc truyện, quiz, dashboard của nhau.
- [ ] Tạo truyện demo khi không có Gemini key, có nhãn nguồn demo.
- [ ] Tạo chương tiếp theo, refresh trang vẫn thấy dữ liệu.
- [ ] Lưu từ, làm quiz đúng/sai, xem mastery/XP/streak.
- [ ] Phân trang lịch sử, dashboard và danh sách admin.
- [ ] Giao diện mobile: hamburger, layout, form, nút và theme.
- [ ] Google Sign-In với OAuth origin hợp lệ (khi có cấu hình).
- [ ] SMTP reset, token hết hạn, token dùng một lần (khi có cấu hình).
- [ ] Non-admin bị từ chối truy cập `/admin/*`.

## Ghi nhận kết quả

Lưu ngày chạy, OS/Python version, commit hash, lệnh, số passed/failed, ảnh Swagger/UI và log đã loại bỏ bí mật. Không ghi PASS khi chưa chạy test thực tế.
