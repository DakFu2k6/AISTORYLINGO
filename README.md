# ✦ AI StoryLingo — Interactive AI Language Learning Web App

> **Dự án Web MidTerm:** Nền tảng học ngoại ngữ qua truyện tương tác thông minh kết hợp trí tuệ nhân tạo (Google Gemini AI), tra cứu từ vựng theo ngữ cảnh (Web Speech API) và ôn tập trắc nghiệm ngắt quãng (Spaced-Repetition Quiz).

---

## 📑 MỤC LỤC
1. [Kiến trúc & Công nghệ](#1-kiến-trúc--công-nghệ)
2. [Cấu trúc thư mục dự án](#2-cấu-trúc-thư-mục-dự-án)
3. [Bảng tra cứu các thông tin cần lấy & Nơi lấy để điền vào .env](#3-bảng-tra-cứu-các-thông-tin-cần-lấy--nơi-lấy-để-điền-vào-env)
4. [Hướng dẫn cài đặt & Khởi chạy Local chi tiết từng bước](#4-hướng-dẫn-cài-đặt--khởi-chạy-local-chi-tiết-từng-bước)
5. [Hướng dẫn cấp quyền Quản trị viên (Admin)](#5-hướng-dẫn-cấp-quyền-quản-trị-viên-admin)
6. [Kịch bản Demo & Kiểm thử toàn bộ tính năng](#6-kịch-bản-demo--kiểm-thử-toàn-bộ-tính-năng)
7. [Chẩn đoán & Xử lý sự cố thường gặp (Troubleshooting)](#7-chẩn-đoán--xử-lý-sự-cố-thường-gặp-troubleshooting)

---

## 1. KIẾN TRÚC & CÔNG NGHỆ

- **Frontend:** Single Page Application (SPA) viết bằng **HTML5 Semantic**, **CSS3** (hỗ trợ 2 chế độ: Dark Mode vũ trụ và Light Mode Warm Slate chống chói mắt), **JavaScript ES6+** thuần (không dùng React, Vue, jQuery để tối ưu tốc độ và tuân thủ yêu cầu đề bài).
- **Backend:** **FastAPI (Python 3.10+)**, **SQLModel / SQLAlchemy**, **Uvicorn**, **Bcrypt** (bảo mật mật khẩu), **Google Identity Services (GSI)**.
- **Cơ sở dữ liệu:** **SQLite** mặc định (`backend/storylingo.db`), tự động khởi tạo bảng và tự động migrate khi chạy, hỗ trợ nâng cấp lên **PostgreSQL / Supabase**.
- **AI Engine:** **Google GenAI SDK** (mô hình `gemini-2.5-flash`), tích hợp sẵn cơ chế **Auto-Fallback về bộ truyện Demo** hoàn chỉnh nếu máy chưa có API key.

---

## 2. CẤU TRÚC THƯ MỤC DỰ ÁN

```text
AISTORYLINGO/
├── .env.example              # File mẫu cấu hình biến môi trường
├── .gitignore                # Khai báo các file loại trừ khỏi Git (.env, *.db, venv)
├── README.md                 # Bộ tài liệu & Cẩm nang hướng dẫn chính thức
├── docs/                     # Tài liệu kiến trúc, xác thực và nâng cấp
│   ├── ARCHITECTURE.md
│   ├── AUTH_SETUP.md
│   └── UPGRADE_GUIDE_VI.md
├── frontend/                 # Mã nguồn Giao diện (SPA)
│   ├── index.html            # Cấu trúc HTML chính
│   ├── style.css             # Giao diện chính (Cosmic Night & Warm Slate)
│   ├── auth.css              # Định kiểu khung đăng nhập và nút Google
│   ├── api.js                # Bộ bọc gọi Fetch API tập trung
│   ├── app.js                # Bộ điều khiển Router SPA, Audio và Logic sự kiện
│   └── terms.html            # Trang Điều khoản sử dụng & Quyền riêng tư
└── backend/                  # Mã nguồn Máy chủ API (FastAPI)
    ├── requirements.txt      # Thư viện Python cần thiết
    ├── requirements-dev.txt  # Thư viện phục vụ kiểm thử (pytest)
    ├── manage_admin.py       # Công cụ cấp quyền Quản trị viên (Admin)
    ├── check.py              # Script kiểm tra kết nối Gemini AI
    ├── app/
    │   ├── main.py           # Điểm khởi chạy FastAPI, CORS và Lifespan
    │   ├── database.py       # Quản lý kết nối SQLite và Auto-migration
    │   ├── models.py         # Định nghĩa các thực thể bảng SQLModel
    │   ├── security.py       # Quản lý mật mã bcrypt, SHA-256 Bearer Token
    │   └── routes/           # Các Router API (auth, stories, quiz, dashboard, admin)
    └── tests/                # Bộ kiểm thử tự động (Unit & Integration Tests)
```

---

## 3. BẢNG TRA CỨU CÁC THÔNG TIN CẦN LẤY & NƠI LẤY ĐỂ ĐIỀN VÀO .ENV

File [**`.env`**](file:///D:/Web%20design/AISTORYLINGO/.env) nằm ở thư mục gốc chứa các khóa bí mật. Dưới đây là hướng dẫn lấy từng thông số:

| Tên biến trong `.env` | Mục đích | Bắt buộc không? | Lấy ở đâu? Cách lấy chi tiết |
|:---|:---|:---:|:---|
| **`GEMINI_API_KEY`** | Dùng AI Google sinh truyện mới theo chủ đề | Không *(có sẵn Demo Story)* | **[Google AI Studio](https://aistudio.google.com/app/apikey)**<br>1. Đăng nhập tài khoản Google.<br>2. Bấm nút **Create API key**.<br>3. Chọn một Project bất kỳ rồi bấm **Create key in existing project**.<br>4. Copy đoạn mã bắt đầu bằng `AIzaSy...` và dán vào. |
| **`GOOGLE_CLIENT_ID`** | Hiển thị nút "Đăng nhập bằng Google" | Không *(vẫn đăng nhập được bằng Email/Username)* | **[Google Cloud Console](https://console.cloud.google.com/)** *(Xem hướng dẫn chi tiết mục 3.1 bên dưới)* |
| **`DATABASE_URL`** | Kết nối cơ sở dữ liệu | Không *(để trống sẽ dùng SQLite tự động)* | **Để trống** để hệ thống tự tạo file `backend/storylingo.db`. Nếu dùng Supabase: vào **Project Settings $\rightarrow$ Database $\rightarrow$ Connection string (URI)**. |
| **`CORS_ORIGINS`** | Cho phép trình duyệt gọi API | **Có** | Mặc định điền: `http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000,http://127.0.0.1:3000` |
| **`FRONTEND_URL`** | Tạo link khôi phục mật khẩu gửi qua email | **Có** | Mặc định điền: `http://localhost:5500` |
| **`SMTP_*`** | Gửi email link reset mật khẩu khi bấm "Forgot password" | Không *(chỉ cần nếu muốn test tính năng gửi mail thật)* | Dùng **Mật khẩu ứng dụng Gmail (Gmail App Password)** *(Xem hướng dẫn mục 3.2)*. Nếu không điền, bấm quên mật khẩu web sẽ báo 503 thông báo hệ thống gửi mail chưa được cấu hình. |

---

### 3.1. Hướng dẫn chi tiết 5 bước lấy Google Client ID (Google Sign-In)
1. Truy cập: **[https://console.cloud.google.com/](https://console.cloud.google.com/)**
2. Bấm vào ô chọn Project ở góc trên bên trái $\rightarrow$ Chọn **New Project** $\rightarrow$ Đặt tên: `AI-StoryLingo` $\rightarrow$ Bấm **Create**.
3. Cấu hình màn hình chấp thuận (**OAuth consent screen**):
   * Ở thanh tìm kiếm trên cùng gõ `OAuth consent screen` $\rightarrow$ Chọn kết quả đầu tiên.
   * Chọn loại người dùng: **External** $\rightarrow$ Bấm **Create**.
   * Điền **App name**: `AI StoryLingo`, chọn **User support email** là email của bạn, điền **Developer contact information** là email của bạn.
   * Bấm **Save and continue** qua bước Scopes.
   * Ở mục **Test users**: Bấm **+ ADD USERS** $\rightarrow$ Nhập chính email Google mà bạn sẽ dùng để test đăng nhập $\rightarrow$ Bấm **Save and continue**.
4. Tạo thông tin xác thực (**Credentials**):
   * Vào menu **APIs & Services $\rightarrow$ Credentials** ở thanh bên trái.
   * Bấm nút **+ CREATE CREDENTIALS** ở trên cùng $\rightarrow$ Chọn **OAuth client ID**.
   * Mục **Application type**: Chọn **Web application**.
   * Mục **Name**: Đặt tên `StoryLingo Web`.
   * **Mục Authorized JavaScript origins (BẮT BUỘC):**
     Bấm **+ ADD URI** thêm dòng thứ nhất: `http://localhost:5500`
     Bấm **+ ADD URI** thêm dòng thứ hai: `http://127.0.0.1:5500`
     *(Lưu ý: Tuyệt đối không để dấu gạch chéo `/` ở cuối URL)*.
   * Bấm **CREATE**.
5. Copy đoạn **Client ID** có đuôi dạng `xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com` dán vào file `.env`:
   ```dotenv
   GOOGLE_CLIENT_ID=xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com
   ```

---

### 3.2. Hướng dẫn lấy thông số SMTP gửi mail qua Gmail (Tùy chọn)
Nếu bạn muốn trải nghiệm tính năng gửi link khôi phục mật khẩu về hòm thư thật:
1. Vào tài khoản Google của bạn: [https://myaccount.google.com/security](https://myaccount.google.com/security)
2. Bật **Xác minh 2 bước (2-Step Verification)** nếu chưa bật.
3. Ở ô tìm kiếm của Google Account, gõ chữ: `App passwords` (Mật khẩu ứng dụng).
4. Đặt tên ứng dụng là `StoryLingo` $\rightarrow$ Bấm **Create**. Google sẽ cấp 1 mã gồm 16 chữ cái (ví dụ: `abcd efgh ijkl mnop`).
5. Điền vào `.env`:
   ```dotenv
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_STARTTLS=true
   SMTP_USER=email-cua-ban@gmail.com
   SMTP_PASSWORD=abcdefghijklmnop
   SMTP_FROM=email-cua-ban@gmail.com
   ```

---

## 4. HƯỚNG DẪN CÀI ĐẶT & KHỞI CHẠY LOCAL CHI TIẾT TỪNG BƯỚC

Yêu cầu máy tính đã cài đặt **Python 3.10 trở lên**.

### Bước 1: Chuẩn bị file cấu hình môi trường
Mở PowerShell / Terminal tại thư mục dự án `AISTORYLINGO`:
```powershell
Copy-Item .env.example .env
```
*(Nếu trên Linux/macOS: gõ `cp .env.example .env`)*.
Mở file `.env` vừa tạo để điền các thông số bạn có (hoặc để nguyên mặc định để chạy thử với Demo Story và SQLite).

---

### Bước 2: Khởi chạy Backend (Mở Terminal 1)
Mở cửa sổ Terminal thứ nhất tại thư mục dự án, vào thư mục `backend`:

```powershell
cd backend

# 1. Tạo môi trường ảo
python -m venv .venv

# 2. Cài đặt các thư viện cần thiết
.\.venv\Scripts\pip.exe install -r requirements.txt

# 3. Khởi chạy máy chủ API
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

> 💡 **Khắc phục lỗi nếu lệnh trên báo lỗi không tìm thấy python hoặc venv:**
> Bạn có thể chạy trực tiếp bằng Python đã cài trên hệ thống máy của bạn:
> ```powershell
> python -m pip install -r requirements.txt
> python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
> ```

Khi thấy terminal hiển thị:
```text
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```
👉 **Backend đã chạy thành công! Hãy giữ nguyên cửa sổ Terminal này.**
- Kiểm tra trạng thái máy chủ: Mở trình duyệt vào [http://localhost:8000/health](http://localhost:8000/health) (hiện `{"status":"ok"}`).
- Xem trang Swagger UI thử nghiệm API: [http://localhost:8000/docs](http://localhost:8000/docs).

---

### Bước 3: Khởi chạy Frontend (Mở Terminal 2)
Mở một cửa sổ Terminal thứ hai tại thư mục dự án, di chuyển vào thư mục `frontend`:

```powershell
cd frontend
python -m http.server 5500
```
*(Cách khác: Mở thư mục dự án bằng VS Code, click chuột phải vào file `frontend/index.html` $\rightarrow$ chọn **Open with Live Server**).*

👉 Mở trình duyệt web truy cập địa chỉ: **[http://localhost:5500](http://localhost:5500)**.

> ⚠️ **Lưu ý:** Không mở web bằng cách click đúp chuột trực tiếp vào file `index.html` trong File Explorer (`file:///...`), vì trình duyệt sẽ kích hoạt cơ chế bảo mật chặn CORS và không kết nối được tới API.

---

## 5. HƯỚNG DẪN CẤP QUYỀN QUẢN TRỊ VIÊN (ADMIN)

Ứng dụng có sẵn một trang Quản trị viên ẩn để theo dõi các số liệu tổng quan (tổng số tài khoản, số lượt làm quiz, số truyện đã sinh) và danh sách người học có phân trang.

Để cấp quyền Admin cho tài khoản của bạn:
1. Mở web `http://localhost:5500`, chuyển sang tab **Create account**, đăng ký một tài khoản mới (ví dụ: `admin@gmail.com`).
2. Mở một cửa sổ Terminal tại thư mục `backend` và chạy lệnh nội bộ:
   ```powershell
   .\.venv\Scripts\python.exe manage_admin.py admin@gmail.com
   ```
   Terminal sẽ báo: `Administrator role granted. Log in again.`
3. Quay lại trình duyệt, đăng nhập lại bằng tài khoản đó: Nút **Admin** sẽ xuất hiện trên thanh điều hướng Topbar!

---

## 6. KỊCH BẢN DEMO & KIỂM THỬ TOÀN BỘ TÍNH NĂNG

Để có một buổi báo cáo đồ án hoặc kiểm tra toàn diện, bạn hãy thao tác theo kịch bản chuẩn 6 bước sau:

1. **Kiểm tra Chế độ Sáng / Tối (Theme Switcher):**
   * Bấm vào icon bóng đèn 💡 ở góc trên bên phải thanh Topbar để chuyển đổi qua lại giữa Dark Mode (Cosmic Night) và Light Mode (Warm Slate chống chói mắt).
2. **Đăng nhập & Đăng ký:**
   * **Màn Log in:** Không yêu cầu tick checkbox điều khoản, đăng nhập nhanh gọn bằng Email hoặc Username.
   * **Màn Create account:** Xuất hiện checkbox điều khoản sử dụng, bắt buộc tick mới tạo được tài khoản.
   * **Đăng nhập Google:** Nếu đã cấu hình Client ID, bấm nút "Đăng nhập bằng Google" để đăng nhập an toàn trong 1 chạm.
3. **Tạo truyện học ngoại ngữ:**
   * Chọn ngôn ngữ (Tiếng Anh / Nhật / Hàn), Trình độ (A1 đến B2), Thể loại (Fantasy, Sci-Fi...), nhập Chủ đề (ví dụ: `space adventure`), chọn số từ vựng (5 từ) và số chương (3 chương).
   * Bấm **✨ Generate story**. Nếu có API key thật, AI Gemini sẽ sáng tác truyện mới; nếu chưa có key, hệ thống tự động tải truyện Demo mẫu gắn nhãn "Demo story".
4. **Đọc truyện tương tác & Nghe phát âm (Reader):**
   * Trong nội dung truyện, các từ vựng mục tiêu được làm nổi bật màu vàng.
   * Bấm vào bất kỳ từ vựng nào: Popup sẽ hiện lên đầy đủ phiên âm quốc tế IPA, từ loại, định nghĩa tiếng Anh, nghĩa tiếng Việt và câu ví dụ.
   * Bấm nút **🔊 Listen**: Trình duyệt sẽ phát âm từ vựng chuẩn ngữ điệu bản xứ (sử dụng Web Speech API).
   * Bấm **+ Save word**: Lưu từ vào sổ tay cá nhân.
   * Cuối chương truyện, đọc 3 phương án rẽ nhánh và bấm chọn 1 hướng đi để mở tiếp Chương 2 và Chương 3.
5. **Luyện tập Spaced-Repetition Quiz:**
   * Sau khi đọc xong truyện, bấm nút **Take the quiz** hoặc bấm tab **Quiz** trên thanh Topbar.
   * Trả lời các câu hỏi trắc nghiệm 4 đáp án (gồm câu hỏi đoán nghĩa và câu hỏi điền từ vào chỗ trống).
   * Trả lời đúng: Được cộng **+20% Mastery** và **+10 XP**; trả lời sai: Bị trừ **-10% Mastery** và nhận **+2 XP** khuyến khích.
6. **Xem Tiến độ học tập (Progress Dashboard):**
   * Bấm tab **Progress**: Xem số ngày streak liên tục 🔥, cấp độ Level, tổng XP, số từ đã thuộc lòng (Mastery $\ge 60\%$), danh sách sổ tay từ vựng và lịch sử các bộ truyện đã học kèm nút đọc lại.

---

## 7. CHẨN ĐOÁN & XỬ LÝ SỰ CỐ THƯỜNG GẶP (TROUBLESHOOTING)

| Hiện tượng | Nguyên nhân | Cách khắc phục |
|:---|:---|:---|
| **`Cannot reach the backend at http://localhost:8000. Is the server running?`** | Chưa bật Backend ở Terminal 1 hoặc cửa sổ terminal đó đã bị tắt. | Mở lại Terminal 1, vào thư mục `backend` và chạy lệnh: `uvicorn app.main:app --reload --port 8000`. |
| **Nút "Sign in with Google" không hiển thị** | Biến `GOOGLE_CLIENT_ID` trong `.env` chưa có giá trị. | Điền Client ID theo hướng dẫn mục 3.1 rồi khởi động lại backend. *(Hoặc đăng nhập bằng Email/Username)*. |
| **Lỗi Google: `origin_mismatch` hoặc `400` khi bấm đăng nhập Google** | Chưa thêm đúng cổng trong Authorized JavaScript origins trên Google Cloud. | Vào lại Google Cloud Console $\rightarrow$ Credentials $\rightarrow$ kiểm tra xem đã thêm chính xác `http://localhost:5500` và `http://127.0.0.1:5500` chưa (không có dấu `/` ở cuối). |
| **Lỗi PowerShell: `Execution_Policies` khi chạy venv** | Windows chặn chạy file script PowerShell chưa ký số. | Không dùng lệnh `activate`. Hãy gọi trực tiếp file `.exe` như hướng dẫn: `.\.venv\Scripts\uvicorn.exe ...` hoặc `.\.venv\Scripts\pip.exe ...`. |
| **Bấm "Forgot password" báo lỗi 503** | Chưa cấu hình thông số hòm thư `SMTP_*` trong file `.env`. | Đây là thiết kế an toàn của hệ thống để không làm lộ token ra trình duyệt. Hãy cấu hình SMTP Gmail theo mục 3.2 để nhận email thật. |
