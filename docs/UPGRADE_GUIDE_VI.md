# Hướng dẫn nâng cấp AI StoryLingo — Web MidTerm

## 1. Những lỗi đã xác định và cách sửa

| Vấn đề trong source gốc | Hệ quả | File và cách sửa |
|---|---|---|
| Login chỉ trả thông tin user, chưa có session | Trình duyệt tự gửi ID của bất kỳ người dùng nào | `security.py`, `routes/auth.py`: session Bearer ngẫu nhiên, chỉ lưu SHA-256 của token, hết hạn sau 24 giờ |
| Các API học tin vào `user_id` do client cung cấp | Xem dashboard/history, làm quiz hoặc lưu từ của người khác | `main.py` gắn dependency `protect_learning`; đối chiếu session với user, story và vocabulary tại backend |
| Quiz lấy câu hỏi theo story ID mà không kiểm tra chủ sở hữu | Lộ nội dung học của người khác | Dependency kiểm tra story trước khi thực thi route |
| Validate email chỉ kiểm tra dấu `@` | Chấp nhận địa chỉ thiếu cấu trúc cơ bản | `auth.py` normalize khoảng trắng/chữ thường, kiểm tra cú pháp; frontend kiểm tra tương ứng |
| Chưa có chính sách password/giới hạn thử đăng nhập | Đăng ký mật khẩu yếu, thử sai liên tục | Đăng ký/reset: ít nhất 8 ký tự, có chữ Latin và số, tối đa 72 byte UTF-8; bcrypt; throttle theo IP/email |
| Service đọc `characters`, `setting` nhưng `FirstChapter` thiếu hai trường | Có thể lỗi 500 khi tạo truyện hoặc rơi vào demo dù AI trả lời được | `ai_engine/schemas.py` bổ sung trường và default; tests AI chạy lại |
| File cấu hình ở gốc nhưng database chỉ nạp `backend/.env` | Cấu hình không được đọc như mong đợi | `database.py` đọc `.env` gốc và hỗ trợ vị trí cũ |
| Danh sách progress trả toàn bộ dữ liệu | Trang dài, payload và truy vấn tăng | `dashboard.py`: COUNT/offset/limit, thống kê toàn bộ tách khỏi trang đang hiển thị |
| Navigation chưa có menu mobile | Các nút chen chúc trên điện thoại | `index.html`, `style.css`, `app.js`: hamburger với `aria-expanded`, đóng khi chọn trang/Escape |
| Không có Google, recovery, admin, điều khoản | Thiếu các yêu cầu giáo viên | Bổ sung API và UI tương ứng, liên kết điều khoản từ login/footer |

**Lưu ý về phạm vi:** đây là bản nâng cấp cho bài nhóm chạy localhost. Admin hiện có thống kê và xem danh sách tài khoản; chưa có chức năng xóa/khóa tài khoản hoặc chỉnh sửa nội dung của người khác.

## 2. Các file nhóm cần ghép

Giải nén gói mới thành một thư mục riêng để so sánh. Các file trong gói đều là phiên bản hoàn chỉnh. Sao lưu bản hiện tại, database và cấu hình trước khi thay.

| File | Trách nhiệm sau nâng cấp |
|---|---|
| `frontend/index.html` | Form đăng nhập, đăng ký, checkbox điều khoản, Google, recovery, các view và navigation |
| `frontend/style.css` | Giao diện sáng tím/xanh, card, input, states, bảng, phân trang, responsive |
| `frontend/api.js` | Gắn Bearer token vào request, xử lý timeout/lỗi, gọi dashboard theo số trang |
| `frontend/app.js` | Điều hướng, xác minh session khi mở lại, Google callback, recovery, admin, hamburger, phân trang |
| `frontend/terms.html` | Điều khoản và thông báo dữ liệu của bài nhóm |
| `backend/app/security.py` | Phát hành/kiểm tra token, current user, role admin, bảo vệ quyền sở hữu |
| `backend/app/routes/auth.py` | Đăng ký/login/logout/me; Google/config/nonce; forgot/reset password |
| `backend/app/routes/admin.py` | API overview và danh sách user phân trang, chỉ dành cho admin |
| `backend/app/routes/dashboard.py` | Dữ liệu cá nhân, thống kê, phân trang hai danh sách độc lập |
| `backend/app/routes/stories.py` | Giữ luồng tạo/đọc/chọn truyện; history có phân trang |
| `backend/app/models.py` | Bổ sung role, Google subject, bảng token và challenge |
| `backend/app/database.py` | Nạp cấu hình, bổ sung cột/index cho database cũ |
| `backend/app/main.py` | Đăng ký router và dependency bảo vệ API |
| `backend/ai_engine/schemas.py` | Đồng bộ dữ liệu AI với service |
| `backend/manage_admin.py` | Cấp quyền admin bằng thao tác local của người quản lý dự án |
| `backend/requirements.txt`, `requirements-dev.txt` | Thư viện chạy và test |
| `backend/tests/` | Test luồng học, AI, quyền truy cập, session, reset, Google giả lập, phân trang |
| `.env.example` | Mẫu cấu hình không có mật khẩu/API key cá nhân |
| `README.md`, `docs/` | Cách chạy và giải thích kiến trúc |

`quiz.py`, `vocabulary.py`, các service và prompts vẫn được dùng. Chúng được bảo vệ bởi dependency chung khi router được đăng ký trong `main.py`; không cần lặp lại cùng một đoạn xác thực ở từng hàm.

## 3. Chạy từ đầu trên Windows

1. Giải nén và mở thư mục `AiStoryLingo` bằng VS Code.
2. Copy `.env.example` thành `.env` tại thư mục gốc.
3. Terminal thứ nhất:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

4. Terminal thứ hai, bắt đầu tại thư mục gốc:

```powershell
cd frontend
python -m http.server 5500
```

5. Truy cập `http://localhost:5500`. Đăng ký với checkbox đồng ý điều khoản.
6. Tạo truyện. Chưa có Gemini key thì dùng demo có gắn nhãn, vẫn kiểm tra được luồng đọc/lưu từ/quiz/progress.

Không cần activate venv. Nếu đổi cổng frontend, phải sửa đồng thời `CORS_ORIGINS`, `FRONTEND_URL` và origin cấu hình Google. Nếu đổi cổng backend, mở DevTools Console của trang và đặt:

```javascript
localStorage.setItem('storylingo_api', 'http://localhost:8001');
location.reload();
```

Để trở về mặc định:

```javascript
localStorage.removeItem('storylingo_api');
location.reload();
```

## 4. Giữ database và tài khoản cũ

- Dừng server cũ; sao lưu `backend/storylingo.db` trước.
- Copy database cũ vào `backend/storylingo.db` của bản mới khi cả hai server đã dừng.
- Để `DATABASE_URL=` trống nếu đang dùng SQLite. Nếu nhóm đã dùng PostgreSQL, giữ URL kết nối thật trong `.env` riêng.
- Khi startup, SQLModel tạo các bảng mới; `ensure_columns()` thêm các cột còn thiếu và unique index của Google subject.
- Mật khẩu bcrypt cũ vẫn dùng để login. Không ép mật khẩu cũ theo quy tắc đăng ký mới; khi reset sẽ áp dụng quy tắc mới.
- Cần đăng nhập lại: localStorage của phiên bản cũ không phải bằng chứng xác thực.
- Đây là migration bổ sung đơn giản, chưa thay thế hệ thống migration có version như Alembic. Với PostgreSQL, tài khoản DB phải có quyền tạo bảng/index và thêm cột. Bản bàn giao được test tự động trên SQLite; nhóm cần kiểm tra lại trên PostgreSQL thật nếu dùng.

## 5. Google Sign-In

### Chuẩn bị

Trong Google Cloud Console của nhóm:

1. Tạo hoặc chọn Google Cloud project.
2. Cấu hình Google Auth Platform/OAuth consent: tên ứng dụng, email hỗ trợ và audience theo tài khoản nhóm.
3. Nếu ở Testing, thêm email thử nghiệm của các thành viên khi cấu hình yêu cầu.
4. Tạo OAuth Client ID loại **Web application**.
5. Thêm **Authorized JavaScript origin** `http://localhost:5500`. Nếu thực sự dùng `127.0.0.1`, thêm riêng `http://127.0.0.1:5500`.
6. Copy Client ID vào `.env`:

```dotenv
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
FRONTEND_URL=http://localhost:5500
CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```

7. Restart backend, reload trang. Nút Google do Google Identity Services render sẽ xuất hiện.

Luồng này dùng JavaScript callback nhận ID token, không dùng OAuth redirect callback nên không cần tự tạo route redirect hoặc đưa Client Secret vào code. Client ID là định danh công khai; Client Secret, mật khẩu SMTP và Gemini key không được đặt ở frontend.

### Cách hoạt động

`GET /auth/google/nonce` tạo challenge 5 phút → frontend đưa nonce cho Google → callback gửi credential + nonce về `/auth/google` → backend dùng `google-auth` kiểm tra token/chữ ký/audience/hạn sử dụng, email verified và nonce → ánh xạ theo Google `sub` → cấp session riêng của ứng dụng.

Tài khoản Google mới phải đồng ý điều khoản. Google subject (`sub`) là định danh liên kết chính; không tự gộp tài khoản chỉ vì trùng email. **Nếu đã đăng ký bằng email/password, dùng password hoặc reset để đăng nhập tài khoản đó; bản này chưa cung cấp chức năng liên kết Google với tài khoản password có sẵn.** Đây là lựa chọn tránh gộp tài khoản nhầm; không phải lỗi password. Hãy dùng email Google chưa đăng ký để demo lần đầu.

Challenge hết hạn hoặc đã dùng sẽ bị từ chối; reload trang để lấy challenge mới. Backend trả 503 nếu nhóm chưa cấu hình Google Client ID. Test tự động mock phần xác minh token; cần thử thực tế bằng tài khoản của nhóm sau khi cấu hình.

Tài liệu chính thức: https://developers.google.com/identity/gsi/web/guides/verify-google-id-token

## 6. Quên mật khẩu qua email

Điền thông tin mail server được nhóm phép dùng:

```dotenv
SMTP_HOST=smtp.your-provider.example
SMTP_PORT=587
SMTP_STARTTLS=true
SMTP_USER=your-mailbox@example.com
SMTP_PASSWORD=your-provider-app-password
SMTP_FROM=your-mailbox@example.com
FRONTEND_URL=http://localhost:5500
```

`SMTP_FROM` phải là người gửi được mail provider chấp thuận. Nếu dùng Gmail SMTP, sử dụng cấu hình và app password phù hợp của tài khoản; không nhập mật khẩu email cá nhân vào frontend. Với mail catcher cục bộ, có thể đặt host/port của nó và `SMTP_STARTTLS=false`, để trống user/password; chỉ dùng cấu hình này ở môi trường local.

Luồng: nhập email → backend tạo token ngẫu nhiên, chỉ lưu hash và hạn 15 phút → gửi link tới email → người dùng mở link → nhập/nhập lại password → token được tiêu thụ một lần → thu hồi mọi phiên/reset token của tài khoản → đăng nhập lại.

- Không có SMTP: báo chưa cấu hình, không giả vờ gửi thành công.
- Email không tồn tại: trả cùng thông báo chung như email tồn tại.
- SMTP gửi lỗi: ghi lỗi vận hành ở backend, hủy token mới, vẫn trả thông báo chung để tránh tiết lộ tài khoản qua nội dung phản hồi. Nhóm kiểm tra server log/mail catcher khi demo gửi thư.
- Không có đường tắt trả token trong API hoặc ghi link reset vào log.
- Trang đọc token rồi loại query khỏi thanh địa chỉ; dùng referrer policy `no-referrer`.
- Reset password chỉ đổi phương thức password; tài khoản Google đã liên kết vẫn có thể dùng Google.

## 7. Admin dashboard

1. Đăng ký tài khoản nhóm trưởng qua giao diện.
2. Mở terminal tại `backend`, dùng cùng `.env`/database của server:

```powershell
.\.venv\Scripts\python.exe manage_admin.py leader@example.com
```

3. Logout rồi login lại để thấy nút **Admin**.

Dashboard có số người dùng, truyện, câu trả lời quiz và từ vựng; bảng tên/email/role có phân trang 10 dòng. `admin_user` kiểm tra role ở server trên từng request; người dùng thường sửa localStorage hoặc tự gọi `/admin/overview` vẫn nhận 403.

Không có password mặc định; không cấp admin theo email từ frontend. Chỉ người có quyền thao tác code/database trên máy nhóm mới chạy script cấp quyền.

## 8. Phân trang nên đặt ở đâu?

| Vị trí | Kích thước trang | Tham số/API | Lý do |
|---|---:|---|---|
| Progress → My words | 6 | `/dashboard/{id}?words_page=2&stories_page=1&page_size=6` | Từ vựng tăng theo thời gian; chuyển trang từ không làm mất trang truyện |
| Progress → My stories | 6 | `/dashboard/{id}?words_page=1&stories_page=2&page_size=6` | Truyện cũ vẫn truy cập qua Continue/Read again |
| Admin → Registered learners | 10 | `/admin/users?page=2&page_size=10` | Admin không phải tải hết tài khoản |
| Story history API | Mặc định 6, tối đa 50 | `/stories/history/{id}?page=2&page_size=6` | Sẵn cho nhóm mở rộng màn thư viện truyện |

Số trang bắt đầu từ 1, page_size từ 1–50. Backend sắp xếp cố định bằng ID/created_at, dùng `offset` và `limit`. Tổng thống kê được tính trên **toàn bộ dữ liệu của user**, không phải chỉ sáu dòng ở trang hiện tại. Các nút Previous/Next tự khóa ở biên. Trang vượt số cuối trả danh sách rỗng; frontend bình thường chỉ cho chuyển trong khoảng hợp lệ.

Không phân trang nội dung chương ngắn hoặc từng câu quiz: reader chia theo chương, quiz đã hiển thị từng câu; đặt pagination tại đó không giúp giải quyết danh sách dài.

API lấy từ đã lưu phục vụ tập ID highlight vẫn trả toàn bộ từ của user; danh sách hiển thị lớn ở Progress dùng API phân trang. Với quy mô lớn nên tách endpoint chỉ trả ID hoặc trạng thái của riêng các từ trong truyện đang mở.

## 9. Đọc code theo luồng

### Đăng nhập và gọi API

`auth-form` → `onAuthSubmit()` → `api.login()` → `POST /auth/login` → normalize email, bcrypt → tạo AuthToken có hash/hạn → trả token một lần → frontend lưu token trong sessionStorage → `request()` tự thêm `Authorization: Bearer ...`.

Khi tải lại trang, `GET /auth/me` xác nhận session trước khi hiển thị thông tin profile lưu tạm. `localStorage.user.id` chỉ phục vụ hiển thị/gọi API, không quyết định quyền. Token hết hạn thì frontend trở về login. Logout vừa thu hồi token ở DB vừa xóa dữ liệu phiên tại trình duyệt.

### Luồng học

Create → request có user_id + Bearer → `protect_learning` xác định user thật → route kiểm tra input → service Gemini/demo → lưu Story/Chapter/Vocabulary → reader highlight từ → lưu từ → quiz kiểm tra chủ sở hữu vocabulary → chấm đáp án/cập nhật XP/mastery → progress tổng hợp và phân trang.

### Các lớp trách nhiệm

- HTML: cấu trúc và semantic controls.
- CSS: màu sắc, bố cục, breakpoint; không gọi API.
- JavaScript: quản lý UI và trạng thái, `api.js` tập trung request HTTP.
- Routes: request/response và điều phối.
- Security dependency: xác thực, role và quyền sở hữu dùng chung.
- Services: AI, progress, giới hạn tạo truyện.
- Models/database: schema và truy vấn/lưu trữ.

Đây là cấu trúc phân lớp nhẹ. Chưa thêm framework frontend/repository abstraction vì bài hiện tại dùng HTML/CSS/JS và SQLModel; giữ khả năng đọc code của cả nhóm.

## 10. Kịch bản demo cho giáo viên

| Bước | Thao tác | Kết quả cần thấy |
|---|---|---|
| 1 | Đăng ký email sai hoặc password yếu | Thông báo rõ; không tạo tài khoản |
| 2 | Đăng ký nhưng chưa đồng ý điều khoản | Bị từ chối |
| 3 | Đăng ký hợp lệ rồi logout/login sai password | Không vào được, không lộ password/hash |
| 4 | Login đúng, tạo truyện, chọn diễn biến | Chapter mới xuất hiện, giữ liên kết truyện/từ |
| 5 | Click từ → Save → Quiz → Progress | Từ được lưu, kết quả cập nhật XP/mastery |
| 6 | Có hơn sáu truyện/từ → Next | Danh sách đổi, tổng thống kê giữ nguyên |
| 7 | DevTools responsive 390px → hamburger | Menu mở/đóng; chọn trang thì tự đóng |
| 8 | Google với email chưa đăng ký, đã cấu hình Client ID | Account được tạo; session dùng chung luồng học |
| 9 | Forgot password với SMTP/mail catcher thật | Nhận link; reset thành công; link cũ không dùng lại |
| 10 | Login admin | Thấy thống kê và bảng user phân trang |
| 11 | Gọi admin API bằng user thường | Backend trả 403 |
| 12 | Thay user_id/story_id của người khác | Backend trả 403 hoặc 404, không trả dữ liệu |

## 11. Kiểm thử và giới hạn bàn giao

Từ backend chạy `python -m pytest -q` bằng Python của venv. Tests dùng DB tạm và không ảnh hưởng dữ liệu nhóm. Bộ test gốc đã được cập nhật để dùng session và yêu cầu password/terms mới; bổ sung tests chống giả user ID, session hết hạn/logout, admin, pagination, reset một lần và Google giả lập.

Kết quả kiểm thử backend cuối cùng được ghi trong `VALIDATION.md`. Luồng giao diện đã được smoke test bằng DOM với backend thật; môi trường không tải được Chromium nên chưa có kiểm tra hiển thị trực quan trên trình duyệt thật. Hãy thực hiện checklist desktop/mobile ở mục 10 trước buổi nộp.

Test Google dùng mock verifier để kiểm tra callback, nonce và audience truyền vào thư viện; không chứng minh cấu hình Google Cloud của nhóm đã đúng. Test email dùng SMTP mock để lấy link và thử reset; không chứng minh email provider thực tế gửi được thư. Gemini thật cần API key/quota; tests AI dùng phản hồi giả lập và demo.

Các giới hạn cần biết trước khi mở rộng:

- Chưa có email verification cho tài khoản password. Không tự gộp với Google account trùng email.
- Throttle là bộ nhớ của một tiến trình; restart sẽ reset. Chạy nhiều worker cần Redis/rate limiter dùng chung. Cấu hình demo dùng một worker.
- Bearer trong sessionStorage phù hợp bản bài tập hiện tại; khi triển khai sản phẩm nên đánh giá HttpOnly cookie, CSRF/CSP và XSS theo kiến trúc triển khai.
- Session/reset/challenge hết hạn không tự dọn định kỳ; truy cập hết hạn vẫn bị từ chối. Có thể bổ sung job xóa các hàng hết hạn khi triển khai lâu dài.
- SQLite/migration đã kiểm thử; PostgreSQL và tích hợp Google/SMTP/Gemini thực tế cần cấu hình và xác minh ở máy nhóm.
- Chưa xử lý đầy đủ tranh chấp khi hai request cùng tạo chương tiếp theo hoặc gửi quiz lặp đồng thời. Bản demo dùng nút busy/disable và kiểm tra chapter hiện có; quy mô nhiều người cần thêm transaction/unique constraints và idempotency.
- Điều khoản là bản nháp cho bài nhóm; cập nhật tên nhóm, kênh liên hệ và chính sách lưu/xóa dữ liệu trước khi phát hành công khai.
- Bản ZIP không mang theo khóa API, mật khẩu hay database người dùng của bản gốc. Giữ chúng riêng, không upload lên GitHub.
