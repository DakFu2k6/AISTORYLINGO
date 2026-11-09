# AI StoryLingo

**Interactive language learning through AI-generated stories** · FastAPI · SQLModel · Vanilla JavaScript · Gemini

AI StoryLingo giúp người học tạo truyện theo chủ đề, ngôn ngữ và trình độ CEFR; quyết định diễn biến từng chương, học từ vựng trong ngữ cảnh, làm quiz và theo dõi tiến bộ. Dự án chạy cục bộ trên Windows/macOS/Linux; không bắt buộc có API key để trải nghiệm chế độ demo.

> **Phạm vi xác nhận:** Hướng dẫn này được đối chiếu với mã nguồn trong bản bàn giao. Chưa xác nhận thành công chạy end-to-end trên máy người dùng. Xem [Báo cáo rà soát](docs/CODE_REVIEW.md).

## 1. Mục lục tài liệu

| Tài liệu | Nội dung |
|---|---|
| [Tổng quan](docs/PROJECT_OVERVIEW.md) | Mục tiêu, tính năng, phạm vi, luồng người dùng |
| [Kiến trúc](docs/ARCHITECTURE.md) | Module, sơ đồ và luồng request |
| [Cài đặt chi tiết](docs/SETUP_GUIDE.md) | Windows PowerShell, Linux/macOS, cấu hình, Google, SMTP, PostgreSQL |
| [API](docs/API_REFERENCE.md) | Endpoint, xác thực, payload và lỗi |
| [Cơ sở dữ liệu](docs/DATABASE.md) | 9 bảng, quan hệ, khởi tạo, backup |
| [AI Engine](docs/AI_ENGINE.md) | Prompt, schema, kiểm tra, fallback |
| [Bảo mật](docs/SECURITY.md) | Xác thực, phân quyền, giới hạn và rủi ro |
| [Kiểm thử](docs/TESTING.md) | Test tự động, checklist thủ công |
| [Vận hành](docs/OPERATIONS.md) | Chẩn đoán lỗi, backup, triển khai |
| [Rà soát mã nguồn](docs/CODE_REVIEW.md) | Những gì đã xác minh và việc cần cải thiện |
| [Google/SMTP](docs/AUTH_SETUP.md) | Ghi chú cấu hình từ bản gốc |
| [Validation](docs/VALIDATION.md) | Ghi chú kiểm chứng từ bản gốc |

## 2. Yêu cầu hệ thống

- Python **3.10+** (khuyến nghị Python 3.11 hoặc 3.12), pip và trình duyệt hiện đại.
- Internet chỉ cần khi dùng Google Sign-In, SMTP hoặc Gemini AI thực.
- Port **8000** (backend) và **5500** (frontend) còn trống.
- SQLite mặc định; PostgreSQL tùy chọn. **Không cần Node.js, npm, Docker hoặc MySQL** để chạy cấu hình mặc định.

## 3. Khởi chạy nhanh — Windows PowerShell

Giải nén và mở PowerShell **tại thư mục `AiStoryLingo`** (nơi có `.env.example`, `backend`, `frontend`).

```powershell
Copy-Item .env.example .env
cd backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Giữ terminal này mở. Mở **terminal thứ hai** từ thư mục `AiStoryLingo`:

```powershell
cd frontend
py -3 -m http.server 5500 --bind 127.0.0.1
```

Truy cập:
- **Ứng dụng:** http://localhost:5500
- **API Swagger:** http://127.0.0.1:8000/docs
- **Health:** http://127.0.0.1:8000/health
- **AI status:** http://127.0.0.1:8000/health/ai

**Lưu ý:** Không mở `index.html` bằng `file://`. Frontend gọi API tại `http://localhost:8000` mặc định. Nếu đã thay cấu hình `localStorage.storylingo_api`, hãy khôi phục URL phù hợp. Hai terminal phải tiếp tục chạy trong khi sử dụng ứng dụng.

## 4. Cấu hình theo nhu cầu

| Mục tiêu | Thao tác |
|---|---|
| Chạy thử không tốn phí AI | Để trống `GEMINI_API_KEY`; truyện dùng dữ liệu demo |
| Gemini AI thật | Đặt `GEMINI_API_KEY` trong `.env` và khởi động lại backend |
| Google Sign-In | Đặt `GOOGLE_CLIENT_ID`, tạo OAuth Web Client và khai báo origin `http://localhost:5500` |
| Quên mật khẩu qua email | Cấu hình SMTP và `FRONTEND_URL` |
| PostgreSQL | Đặt `DATABASE_URL=postgresql://...`; tạo DB trước khi chạy |
| Admin dashboard | Đăng ký tài khoản, sau đó cấp role bằng CLI ở mục 5 |

**Không commit `.env`, mật khẩu, API key, token hoặc file database thật lên Git.** Xem [hướng dẫn đầy đủ](docs/SETUP_GUIDE.md).

## 5. Cấp quyền admin

Sau khi đăng ký tài khoản trong giao diện, mở PowerShell tại `backend`:

```powershell
.\.venv\Scripts\python.exe manage_admin.py user@example.com
```

Đăng xuất và đăng nhập lại. Script tìm người dùng theo **email**, không theo username. Không có tài khoản admin mặc định.

## 6. Kiểm thử

Từ thư mục `backend`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Bài test dùng database thử nghiệm, không cần Gemini API key. Xem [TESTING.md](docs/TESTING.md) để biết phạm vi và checklist chạy thử bằng trình duyệt.

## 7. Dừng và khởi động lại

Nhấn `Ctrl+C` tại từng terminal. Những lần sau chỉ cần chạy lại lệnh `uvicorn` ở terminal backend và `http.server` ở terminal frontend; không cần tạo lại venv hoặc cài lại dependencies nếu không thay đổi chúng. Dữ liệu SQLite được lưu ở `backend/storylingo.db`.

## 8. Khắc phục lỗi nhanh

| Triệu chứng | Cách xử lý |
|---|---|
| `No module named sqlmodel` | Cài `requirements.txt` bằng đúng Python trong `.venv` |
| `Cannot reach backend` | Kiểm tra port 8000, `/health`, `frontend/api.js` và URL API đã lưu trong localStorage |
| CORS error | Dùng `http://localhost:5500` và kiểm tra `CORS_ORIGINS` |
| Google button không hiển thị | Kiểm tra `GOOGLE_CLIENT_ID`, OAuth origin, kết nối Internet và tải lại trang |
| Gemini chỉ tạo demo | Kiểm tra `/health/ai`, API key, quota, model và log backend |
| Không gửi được email reset | Kiểm tra SMTP host, port, TLS, tài khoản và log server |
| `Address already in use` | Tắt tiến trình đang chiếm port hoặc đổi port đồng bộ frontend/backend/CORS |

Đọc [OPERATIONS.md](docs/OPERATIONS.md) để xử lý chi tiết.

## 9. Cấu trúc mã nguồn

```text
AiStoryLingo/
├── .env.example             # Mẫu cấu hình, không chứa bí mật
├── backend/
│   ├── ai_engine/           # Prompt và schema đầu ra AI
│   ├── app/
│   │   ├── routes/          # Auth, stories, vocabulary, quiz, dashboard, admin
│   │   ├── services/        # AI, demo, progress, rate limit
│   │   ├── database.py      # Engine và khởi tạo bảng
│   │   ├── models.py        # SQLModel entities
│   │   ├── security.py      # Bearer token, quyền truy cập
│   │   └── main.py          # FastAPI entry point
│   ├── tests/               # pytest
│   ├── manage_admin.py      # Cấp quyền admin từ CLI
│   └── requirements*.txt
├── frontend/                # HTML, CSS, JS, terms
└── docs/                    # Tài liệu kỹ thuật và vận hành
```

## 10. Giới hạn hiện tại

Dự án hướng đến demo/học tập và chạy cục bộ; **không coi là production-ready** khi chưa xử lý các khuyến nghị trong [CODE_REVIEW.md](docs/CODE_REVIEW.md), thiết lập HTTPS, backup, quản lý secrets, migration chính thức, monitoring và kiểm thử triển khai thực tế.
