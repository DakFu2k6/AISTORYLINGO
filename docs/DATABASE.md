# Thiết kế cơ sở dữ liệu

## Engine

`backend/app/database.py` đọc `.env` ở thư mục gốc trước, sau đó `backend/.env` chỉ bổ sung biến chưa có. `DATABASE_URL` trống dùng SQLite tại `backend/storylingo.db`; URL PostgreSQL dùng `postgresql://user:password@host:5432/database`. Tạo database PostgreSQL trước khi chạy backend. Không dùng MySQL trong cấu hình được tài liệu hóa.

## Danh mục bảng (đối chiếu `backend/app/models.py`)

| Bảng | Khóa chính | Nội dung và liên kết |
|---|---|---|
| `users` | `id` (string) | name, username, email, role, google_sub, password_hash |
| `user_stats` | `user_id` | FK → users; XP, streak, last_active |
| `stories` | `id` | FK `user_id` → users; metadata, source, status, context |
| `chapters` | `id` | FK `story_id` → stories; chapter_number, content, choices |
| `vocabulary` | `id` | FK `story_id` → stories; word, meaning, example |
| `user_vocabulary` | `id` | FK user_id → users, vocabulary_id → vocabulary; mastery |
| `quiz_results` | `id` | FK user_id, vocabulary_id, story_id; answer, is_correct |
| `auth_tokens` | `digest` | FK user_id → users; purpose, expires_at |
| `google_challenges` | `digest` | Nonce hash và expiration |

```mermaid
erDiagram
  users ||--o{ stories : creates
  users ||--o| user_stats : tracks
  users ||--o{ user_vocabulary : saves
  users ||--o{ quiz_results : answers
  users ||--o{ auth_tokens : owns
  stories ||--o{ chapters : contains
  stories ||--o{ vocabulary : introduces
  vocabulary ||--o{ user_vocabulary : learned_as
  vocabulary ||--o{ quiz_results : tested_by
  stories ||--o{ quiz_results : contextualizes
```

## Quy tắc dữ liệu

- `username`, `email`, `google_sub` có ràng buộc unique ở model; email được chuẩn hóa chữ thường ở API đăng ký.
- `chapters.choices` và `stories.context` lưu JSON dạng string; không phải cột JSON native.
- Token được hash trước khi lưu; `password_hash` lưu bcrypt hash, không lưu mật khẩu rõ.
- `create_db_and_tables()` chạy khi app khởi động, `SQLModel.metadata.create_all()` tạo bảng còn thiếu, `ensure_columns()` bổ sung một số cột tương thích từ bản cũ.

## Backup SQLite — khi backend đã dừng

```powershell
Copy-Item backend\storylingo.db backend\storylingo.backup.db
```

Không xóa file database khi cập nhật source. Với PostgreSQL, dùng `pg_dump` và `pg_restore` tương ứng phiên bản PostgreSQL; kiểm tra restore trên môi trường thử nghiệm trước khi nâng cấp.

## Hạn chế cần khắc phục

Không có Alembic migration versioning; schema update tự động chưa bao phủ đổi kiểu, đổi tên cột hoặc ràng buộc phức tạp. Chưa xác minh các ràng buộc uniqueness nghiệp vụ cho `(story_id, chapter_number)` hoặc `(user_id, vocabulary_id)` ở database. Không thay đổi schema thủ công trên dữ liệu thật khi chưa backup.
