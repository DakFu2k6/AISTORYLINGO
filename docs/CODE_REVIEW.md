# Báo cáo rà soát mã nguồn — 2026-11-09

## Phương pháp

Đã kiểm tra cấu trúc và các file mã nguồn trong gói `Web.zip`, gồm frontend, FastAPI routes, SQLModel, AI service, requirements và tests. Đây là **static review**, không phải kiểm thử end-to-end hay pentest.

## Kết quả

| Khu vực | Đánh giá từ source | Ghi chú |
|---|---|---|
| Frontend | Có đủ các màn hình cốt lõi và Google button container | `index.html`, `api.js`, `app.js`; cần kiểm thử trình duyệt |
| Backend | Các router được đăng ký, có auth/role/ownership | `main.py`, `security.py`, `routes/*`; chưa xác nhận runtime |
| AI | Có schema, validation, fallback | `story_service.py`; cần test key thật nếu muốn chứng minh Gemini |
| Database | Có 9 model bảng và tạo schema khi start | Chưa có migration tool versioned |
| Test | Có pytest cho API/security/AI/progress | Cần cài dependencies trước khi chạy |
| Documentation | Đã chuẩn hóa README và docs | Không thay đổi hành vi app trong gói tài liệu này |

## Kiểm thử trong môi trường rà soát

Đã thử `python -m pytest backend/tests -q` trên môi trường hiện tại. Test **không thể bắt đầu** do `ModuleNotFoundError: No module named 'sqlmodel'` (môi trường rà soát chưa cài dependencies). Đây là thiếu thư viện trong môi trường test, **không đủ bằng chứng kết luận source có lỗi**. Chạy lại theo `TESTING.md` sau khi cài `requirements-dev.txt` trong venv.

## Vấn đề và khuyến nghị ưu tiên

1. **P1 — Migration database:** `create_all()` và `ensure_columns()` chưa thay thế Alembic. Backup và migration có version trước khi thay schema.
2. **P1 — Bảo mật production:** rate limit trong memory, thiếu bằng chứng HTTPS/monitoring/security headers; không triển khai công khai nguyên trạng.
3. **P1 — Chạy E2E:** kiểm thử đầy đủ đăng nhập email/username, Google, SMTP, tạo truyện, quiz, admin và phân quyền với hai tài khoản.
4. **P2 — Phụ thuộc:** `requirements.txt` không pin phiên bản; nên lock phiên bản sau khi test tương thích để tránh thay đổi bất ngờ.
5. **P2 — Kiểm thử concurrency:** bảo vệ tính duy nhất chương, từ đã lưu và cập nhật tiến độ khi request lặp/đồng thời.
6. **P2 — Observability:** thêm structured logging, request ID, error monitoring và cảnh báo không lộ secret.
7. **P3 — Frontend maintainability:** `app.js` lớn, có thể tách theo views/features, thêm lint và test JS sau khi ổn định chức năng.

## Kết luận

Kiến trúc phù hợp một đồ án/demo full-stack; chưa có cơ sở tuyên bố “frontend/backend hoàn toàn không lỗi” hoặc “production-ready”. Bản tài liệu mới tập trung hướng dẫn cài đặt, kiến trúc, bảo mật, kiểm thử và bàn giao; mã nguồn ứng dụng được giữ nguyên để tránh sửa ngoài phạm vi khi chưa chạy regression tests.
