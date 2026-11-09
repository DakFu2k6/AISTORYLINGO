# Tham chiếu REST API

**Base URL local:** `http://127.0.0.1:8000` · **Swagger:** `/docs` · **OpenAPI:** `/openapi.json`.

## Xác thực

Các endpoint học tập và admin cần `Authorization: Bearer <access_token>`. Token nhận sau login/register/Google login; thời hạn mặc định 24 giờ. `user_id` gửi ở path/query/body phải khớp tài khoản đã xác thực. Endpoint admin còn kiểm tra `role=admin`.

| Method | Path | Mục đích | Auth |
|---|---|---|---|
| GET | `/` | Thông báo API | Public |
| GET | `/health` | Trạng thái service | Public |
| GET | `/health/ai` | Trạng thái cấu hình AI (`probe=true` để thử gọi) | Public |
| POST | `/auth/register` | Tạo tài khoản | Public |
| POST | `/auth/login` | Login bằng email hoặc username | Public |
| GET | `/auth/me` | User hiện tại | Bearer |
| POST | `/auth/logout` | Thu hồi token hiện tại | Bearer |
| GET | `/auth/config` | Google client ID công khai và trạng thái SMTP | Public |
| GET | `/auth/google/nonce` | Tạo nonce Google | Public |
| POST | `/auth/google` | Xác thực Google ID token | Public |
| POST | `/auth/forgot-password` | Yêu cầu reset qua SMTP | Public |
| POST | `/auth/reset-password` | Đặt mật khẩu mới bằng token | Public |
| POST | `/stories/generate` | Tạo truyện + chương đầu + từ vựng | Bearer |
| POST | `/stories/{story_id}/next-chapter` | Tiếp tục truyện | Bearer |
| GET | `/stories/history/{user_id}` | Lịch sử truyện có phân trang | Bearer |
| GET | `/stories/{story_id}` | Chi tiết truyện; query `user_id` | Bearer |
| POST | `/vocabulary/save` | Lưu từ vựng | Bearer |
| GET | `/vocabulary/user/{user_id}` | Từ đã lưu | Bearer |
| GET | `/quiz/story/{story_id}` | Câu hỏi quiz của truyện | Bearer |
| POST | `/quiz/submit` | Chấm đáp án, cập nhật tiến độ | Bearer |
| GET | `/dashboard/{user_id}` | Dashboard có phân trang | Bearer |
| GET | `/admin/overview` | Thống kê hệ thống | Admin |
| GET | `/admin/users` | Danh sách user có phân trang | Admin |

## Ví dụ request

Đăng ký:

```json
{"name":"Demo Learner","username":"demo_learner","email":"learner@example.com","password":"Example1234","accepted_terms":true}
```

Gửi JSON trên tới `POST /auth/register`; response chứa `user`, `access_token`, `token_type`. Không dùng mật khẩu ví dụ cho tài khoản thực.

Tạo truyện (sau login):

```http
POST /stories/generate
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{"user_id":"<id-from-login>","language":"English","level":"A2","genre":"Adventure","topic":"A lost map","target_words":5,"total_chapters":3}
```

Tiếp tục truyện:

```json
{"user_id":"<id-from-login>","chapter_id":1,"choice":"Follow the river"}
```

Gửi tới `POST /stories/{story_id}/next-chapter`. `choice` cần lấy từ lựa chọn hợp lệ của chương hiện tại.

Phân trang: `GET /stories/history/{user_id}?page=1&page_size=6`; `GET /dashboard/{user_id}?words_page=1&stories_page=1&page_size=6`; `GET /admin/users?page=1&page_size=10`. `page_size` tối đa 50 ở các route có Query constraint.

## HTTP errors

`400` dữ liệu nghiệp vụ không hợp lệ; `401` thiếu/sai/hết hạn token; `403` không đủ quyền hoặc truy cập user khác; `404` resource không tồn tại/không thuộc quyền; `422` Pydantic validation; `429` rate limit; `503` Google/SMTP chưa cấu hình. Chi tiết response thực tế xem `/docs`, vì mỗi route có thể trả lỗi bổ sung.

## Ghi chú tích hợp

Frontend API client ở `frontend/api.js`; timeout HTTP mặc định 90 giây. Không sử dụng trực tiếp API key Gemini từ browser. Các đường dẫn API trên đây được lấy từ decorator trong source, không phải danh sách API đã kiểm thử runtime.
