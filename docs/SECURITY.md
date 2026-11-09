# Bảo mật và quyền truy cập

## Cơ chế hiện có (theo source)

- Mật khẩu local được băm bằng bcrypt, không lưu plaintext.
- Session dùng Bearer token ngẫu nhiên; chỉ SHA-256 digest lưu trong `auth_tokens`, mặc định hết hạn sau 24 giờ; logout thu hồi token.
- Google ID token được backend kiểm tra audience/chữ ký và nonce, kết hợp email đã xác minh.
- Password reset dùng token có hạn 15 phút, một lần sử dụng, thu hồi các session khi đổi mật khẩu.
- `protect_learning` xác minh người dùng và quyền sở hữu truyện/từ vựng; admin endpoint yêu cầu `role=admin`.
- Throttle login, register, Google và reset hiện dựa trên dictionary trong memory của tiến trình Python.
- CORS cho phép các origin trong `CORS_ORIGINS`; không được xem CORS là cơ chế authentication.

## Rủi ro còn lại

1. Throttle in-memory không chia sẻ giữa nhiều worker và mất khi restart; production nên dùng Redis/edge rate limiting.
2. Bearer token nằm trong `sessionStorage`: XSS vẫn có thể lấy token; nên bổ sung CSP, kiểm tra DOM injection và cân nhắc cookie HttpOnly + CSRF protection theo kiến trúc triển khai.
3. `GET /health/ai` công khai trạng thái và lỗi AI; tránh lộ thông tin vận hành chi tiết ở production.
4. Database được tự nâng cấp bằng `ALTER TABLE` giới hạn; cần migration có kiểm soát và backup.
5. Không có chứng cứ về HTTPS, secrets manager, monitoring, vulnerability scanning hoặc security review production.
6. Kiểm tra điều kiện Google Sign-In, origin và tài khoản liên kết khi triển khai domain thật; không để `localhost` trong cấu hình production.
7. Cần thêm kiểm thử cạnh tranh đồng thời cho tạo chương, lưu từ và quiz để tránh cập nhật trùng.

## Checklist trước khi triển khai công khai

- [ ] HTTPS và redirect HTTP→HTTPS; giới hạn trusted hosts/proxy.
- [ ] Không commit `.env`, DB, token hoặc log chứa dữ liệu cá nhân.
- [ ] CORS chỉ gồm domain frontend thật.
- [ ] Rate limit tập trung và audit log sự kiện nhạy cảm.
- [ ] Chạy dependency scan, kiểm tra XSS/CSRF/IDOR, test account isolation.
- [ ] Backup tự động, kiểm tra restore, quy trình rotate secret.
- [ ] Tài khoản DB ít quyền, không chạy service bằng tài khoản quản trị hệ điều hành.
- [ ] Xác minh cấu hình Google/SMTP với domain thật.

**Phạm vi:** Tài liệu là rà soát thiết kế theo source, không phải chứng nhận pentest hay cam kết an toàn production.
