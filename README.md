# ✦ AI StoryLingo — Interactive Language Learning Web App

> **Dự án Web MidTerm:** Ứng dụng học ngoại ngữ qua truyện tương tác thông minh kết hợp AI, sổ tay từ vựng ngữ cảnh và bài tập trắc nghiệm ghi nhớ ngắt quãng (Spaced-Repetition Quiz).

---

## 📌 Công nghệ sử dụng
- **Frontend:** Vanilla HTML5, CSS3, JavaScript ES6+ (kiến trúc Single Page Application - SPA, không phụ thuộc framework).
- **Backend:** FastAPI (Python 3.10+), SQLModel, Uvicorn, Bcrypt, Google Identity Services, Google GenAI SDK.
- **Database:** SQLite mặc định (`backend/storylingo.db`), tự động khởi tạo và nâng cấp bảng khi khởi chạy.
- **AI Engine:** Google Gemini (mô hình `gemini-2.5-flash`), tích hợp cơ chế tự động Fallback về **Demo Story** chất lượng cao nếu chưa có API key.

---

## 📂 Cấu trúc thư mục

```text
AISTORYLINGO/
├── .env.example              # File mẫu cấu hình biến môi trường
├── .gitignore                # Khai báo các file loại trừ khỏi Git (.env, *.db, venv)
├── README.md                 # Hướng dẫn chính thức của dự án
├── docs/                     # Tài liệu thiết kế, bảo mật, xác thực và nâng cấp
│   ├── ARCHITECTURE.md
│   ├── AUTH_SETUP.md
│   └── UPGRADE_GUIDE_VI.md
├── frontend/                 # Giao diện người dùng (SPA)
│   ├── index.html            # Cấu trúc HTML ngữ nghĩa (Semantic HTML)
│   ├── style.css             # Thiết kế giao diện (Dark Cosmic & Warm Slate Light Mode)
│   ├── auth.css              # Định kiểu khung xác thực và nút Google
│   ├── api.js                # Bộ thư viện gọi Fetch API tập trung
│   ├── app.js                # Bộ điều khiển Router SPA, Audio và Logic tương tác
│   └── terms.html            # Trang Điều khoản sử dụng & Quyền riêng tư
└── backend/                  # Máy chủ API (FastAPI)
    ├── requirements.txt      # Thư viện Python cần thiết
    ├── requirements-dev.txt  # Thư viện phục vụ kiểm thử (pytest)
    ├── manage_admin.py       # Script cấp quyền Quản trị viên (Admin)
    ├── check.py              # Script kiểm tra cấu hình Gemini AI
    ├── app/
    │   ├── main.py           # Điểm khởi chạy FastAPI, CORS và Lifespan
    │   ├── database.py       # Quản lý kết nối SQLite và Auto-migration
    │   ├── models.py         # Định nghĩa các thực thể SQLModel
    │   ├── security.py       # Quản lý mã hóa bcrypt và phiên Bearer Token
    │   └── routes/           # Các endpoint API (auth, stories, quiz, dashboard, admin)
    └── tests/                # Bộ kiểm thử tự động toàn diện
```

---

## 🚀 Hướng dẫn cài đặt & Khởi chạy Local (2 Terminal)

Yêu cầu máy tính đã cài đặt **Python 3.10 trở lên**.

### Bước 1: Chuẩn bị file cấu hình môi trường
Mở terminal tại thư mục gốc của dự án (`AISTORYLINGO`):
```powershell
Copy-Item .env.example .env
```
*(Trên macOS/Linux: `cp .env.example .env`)*.

---

### Bước 2: Khởi động Backend (Mở Terminal 1)
Di chuyển vào thư mục `backend`, tạo môi trường ảo và khởi động server FastAPI:

```powershell
cd backend
python -m venv .venv

# Cài đặt các thư viện cần thiết
.\.venv\Scripts\pip.exe install -r requirements.txt

# Khởi chạy máy chủ API
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```
> 💡 **Mẹo:** Lệnh trên gọi trực tiếp `uvicorn.exe` trong `.venv` nên **không cần kích hoạt virtualenv** (`activate`), tránh hoàn toàn lỗi *PowerShell Execution Policy*.

Khi terminal hiển thị:
```text
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```
👉 Server Backend đã sẵn sàng! Giữ nguyên cửa sổ Terminal này.
* Kiểm tra API sống: [http://localhost:8000/health](http://localhost:8000/health) (trả về `{"status":"ok"}`).
* Xem tài liệu API tự động: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI).

---

### Bước 3: Khởi động Frontend (Mở Terminal 2)
Mở một cửa sổ Terminal riêng biệt tại thư mục `frontend`:

```powershell
cd frontend
python -m http.server 5500
```
*(Hoặc trong VS Code: click chuột phải vào file `frontend/index.html` $\rightarrow$ chọn **Open with Live Server**)*.

👉 Mở trình duyệt và truy cập: **[http://localhost:5500](http://localhost:5500)**.

> ⚠️ **Lưu ý quan trọng:** Không mở file `index.html` bằng cách nhấp đúp chuột trực tiếp (`file:///...`), vì trình duyệt sẽ chặn bảo mật CORS. Luôn truy cập qua `http://localhost:5500`.

---

## 🔑 Cấu hình nâng cao (Tùy chọn)

Ứng dụng được thiết kế để **chạy được ngay lập tức** mà không bắt buộc phải có API key:
- **Không cần API key:** Ứng dụng tự động chuyển sang chế độ **Demo Story** có gắn nhãn, cho phép trải nghiệm 100% tính năng tạo truyện, lựa chọn diễn biến rẽ nhánh, lưu từ vựng và làm quiz.

Nếu muốn dùng AI thật hoặc Đăng nhập Google:
1. **Dùng AI Gemini thật:**
   * Mở file `.env` ở thư mục gốc.
   * Điền API key lấy từ Google AI Studio: `GEMINI_API_KEY=AIzaSy...`
   * Lưu lại file và backend sẽ tự động nhận diện.
2. **Bật Đăng nhập bằng Google (Google Sign-In):**
   * Lên Google Cloud Console tạo một **OAuth Client ID** loại **Web Application**.
   * Thêm `http://localhost:5500` và `http://127.0.0.1:5500` vào **Authorized JavaScript origins**.
   * Dán Client ID vào file `.env`:
     ```dotenv
     GOOGLE_CLIENT_ID=xxxxxxxxxxxx.apps.googleusercontent.com
     ```
   * F5 lại trang web: nút **Đăng nhập bằng Google** sẽ xuất hiện ngay lập tức.

---

## 🛡️ Cấp quyền Quản trị viên (Admin Dashboard)

Hệ thống có trang Admin riêng biệt để theo dõi danh sách thành viên và thống kê học tập. Để cấp quyền Admin cho tài khoản của bạn:

1. Đăng ký một tài khoản bình thường trên giao diện web (ví dụ: `myadmin@gmail.com`).
2. Mở Terminal tại thư mục `backend` và chạy lệnh nội bộ:
   ```powershell
   .\.venv\Scripts\python.exe manage_admin.py myadmin@gmail.com
   ```
3. Đăng nhập lại vào web: Mục **Admin** sẽ xuất hiện trên thanh điều hướng Topbar.

---

## 🧪 Chạy Kiểm thử tự động (Unit & Integration Tests)

Mở Terminal tại thư mục `backend`:
```powershell
cd backend
.\.venv\Scripts\pip.exe install -r requirements-dev.txt
.\.venv\Scripts\pytest.exe -v
```
Toàn bộ 10 ca kiểm thử bao quát từ đăng ký, bảo mật bcrypt, chống duplicate story, chống gian lận quiz và tính điểm Spaced Mastery sẽ chạy và vượt qua 100%.

---

## 🛠️ Xử lý sự cố thường gặp (Troubleshooting)

1. **Lỗi `Cannot reach the backend at http://localhost:8000. Is the server running?`:**
   * **Nguyên nhân:** Server Backend ở Terminal 1 chưa được bật hoặc bị tắt.
   * **Xử lý:** Mở lại Terminal 1 và chạy lệnh `uvicorn app.main:app --reload --port 8000`.
2. **Nút Google không hiện:**
   * **Nguyên nhân:** Chưa cấu hình `GOOGLE_CLIENT_ID` trong file `.env`.
   * **Xử lý:** Điền Client ID hoặc đăng nhập bình thường bằng Email/Username + Mật khẩu.
3. **Màn hình sáng bị chói:**
   * Hệ thống đã tích hợp bảng màu **Soft Slate & Warm Paper** dịu mắt. Bấm vào nút bóng đèn 💡 ở góc phải trên cùng để chuyển đổi giữa Dark Mode và Light Mode chống chói.
