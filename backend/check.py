import sys

from dotenv import load_dotenv
from app.database import BACKEND_DIR

load_dotenv(BACKEND_DIR / ".env")

from app.services.story_service import StoryService  # noqa: E402  (after load_dotenv)

service = StoryService()
info = service.describe()

print("Gemini configuration")
print(f"  .env file found : {(BACKEND_DIR.parent / '.env').exists() or (BACKEND_DIR / '.env').exists()}")
print(f"  key loaded      : {info['key_loaded']}")
print(f"  backend         : {info['backend']}   (studio = AI Studio, vertex = Vertex Express)")
print(f"  model           : {info['model']}")
if info["last_error"]:
    print(f"  problem         : {info['last_error']}")

print("Test call")
result = service.probe()
if result["ok"]:
    print(f"  OK. Gemini answered: {result['reply']!r}")
    sys.exit(0)

print(f"  FAILED: {result['error']}")
if service.client is not None and info["backend"] == "studio":
    try:
        names = [m.name for m in service.client.models.list() if "flash" in m.name.lower()]
        print("  Flash models your key can see:", ", ".join(names) or "(none)")
    except Exception as exc:  
        print(f"  Could not list models: {service._explain(exc)}")
sys.exit(1)
