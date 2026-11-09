import sys
from dotenv import load_dotenv
from app.database import BACKEND_DIR

# Tải file .env từ thư mục backend
load_dotenv(BACKEND_DIR / ".env")

from app.services.story_service import StoryService  # noqa: E402

service = StoryService()
info = service.describe()

print("=" * 50)
print("🔍 KIỂM TRA CẤU HÌNH GEMINI HIỆN TẠI")
print("=" * 50)
print(f"  .env file found : {(BACKEND_DIR / '.env').exists()}")
print(f"  Key loaded      : {info['key_loaded']}")
print(f"  Backend mode    : {info['backend']}   (studio = AI Studio, vertex = Vertex Express)")
print(f"  Current model   : {info['model']}")
if info["last_error"]:
    print(f"  Lỗi khởi tạo    : {info['last_error']}")

print("\n" + "=" * 50)
print("🚀 ĐANG QUÉT TOÀN BỘ CÁC MODEL AI CÓ THỂ SỬ DỤNG ĐƯỢC...")
print("=" * 50)

if service.client is None:
    print("❌ Không thể kết nối tới client Gemini do chưa có API Key hợp lệ.")
    sys.exit(1)

try:
    # Liệt kê tất cả các model mà tài khoản / API key này nhìn thấy
    all_models = list(service.client.models.list())
    
    if not all_models:
        print("⚠️ Không tìm thấy model nào khả dụng cho API Key này.")
    else:
        print(f"✨ Tìm thấy tổng cộng {len(all_models)} model khả dụng:\n")
        for m in all_models:
            # Lấy tên định danh và mô tả của model nếu có
            name = getattr(m, "name", str(m))
            supported_actions = getattr(m, "supported_generation_methods", [])
            print(f"  - Model ID: {name}")
            if supported_actions:
                print(f"    Hỗ trợ: {', '.join(supported_actions)}")
            print("-" * 40)
            
except Exception as exc:
    print(f"❌ Không thể liệt kê danh sách model: {service._explain(exc)}")
    sys.exit(1)

print("\n" + "=" * 50)
print("🧪 KIỂM TRA THỬ NGHIỆM GỌI API (PROBE)")
print("=" * 50)
result = service.probe()
if result["ok"]:
    print(f"  ✅ THÀNH CÔNG! AI phản hồi: {result['reply']!r}")
    sys.exit(0)
else:
    print(f"  ❌ THẤT BẠI: {result['error']}")
    sys.exit(1)