# Tổng quan sản phẩm

## Bài toán

Học ngoại ngữ qua nội dung cố định có thể thiếu tính cá nhân hóa và ít cơ hội vận dụng từ mới. AI StoryLingo tạo câu chuyện theo lựa chọn của người học và gắn hoạt động luyện tập với nội dung vừa đọc.

## Vai trò

- **Guest:** xem trang đăng nhập, đăng ký và điều khoản.
- **Learner:** tạo truyện, đọc và chọn hướng đi, lưu từ, làm quiz, xem lịch sử và tiến độ.
- **Admin:** xem thống kê hệ thống và danh sách người dùng có phân trang; không mặc nhiên có quyền đọc nội dung riêng tư của người học qua các API learner.

## Phạm vi chức năng

| Nhóm | Hành vi | Module |
|---|---|---|
| Tài khoản | Đăng ký, email/username login, logout, Google ID token, reset mật khẩu | `routes/auth.py` |
| Truyện | Tạo chương đầu, chọn hướng đi, xem lịch sử, xem chi tiết | `routes/stories.py` |
| Từ vựng | Lưu từ trong truyện, xem danh sách từ đã lưu | `routes/vocabulary.py` |
| Quiz | Câu hỏi nghĩa từ và điền từ, chấm điểm, cập nhật mastery | `routes/quiz.py` |
| Tiến độ | XP, streak, từ và truyện đã học | `routes/dashboard.py`, `services/progress.py` |
| Quản trị | Thống kê tổng, danh sách user có phân trang | `routes/admin.py` |

## Luồng người học

1. Mở website, tạo tài khoản hoặc đăng nhập.
2. Chọn language, CEFR level, genre, topic, số từ và số chương.
3. Backend yêu cầu Gemini tạo chương và từ vựng, hoặc dùng demo khi AI không khả dụng.
4. Đọc chương, chọn một lựa chọn; backend tạo chương tiếp theo và lưu lịch sử.
5. Lưu từ, luyện quiz, xem tiến bộ ở dashboard.

## Tiêu chí nghiệm thu gợi ý

- Người dùng A không đọc/ghi được dữ liệu học của B qua API.
- Truyện có nguồn `gemini` hoặc `demo` được phân biệt.
- Tạo và tiếp tục truyện, lưu từ, quiz, dashboard hoạt động với dữ liệu nhất quán.
- Google login và reset email được kiểm tra riêng khi cấu hình bên ngoài đã sẵn sàng.
- Không có khóa API hay mật khẩu được đưa vào source control.

## Ngoài phạm vi đã xác minh

Không có bằng chứng trong source về mobile app native, thanh toán, triển khai cloud, hàng đợi xử lý AI, giám sát production hoặc quản lý nhiều tổ chức. Không mô tả các chức năng này là đã hoàn thành.
