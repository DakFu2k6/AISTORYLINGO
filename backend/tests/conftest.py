import os
import tempfile
import uuid

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["GEMINI_API_KEY"] = ""
os.environ["GEMINI_MODEL"] = "gemini-2.5-flash"
os.environ["GEMINI_BACKEND"] = "auto"
os.environ["GENERATE_LIMIT_PER_HOUR"] = "0"  

import pytest  
from fastapi.testclient import TestClient  
from app.main import app 
from app.services import rate_limit  

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def _clean_state():
    rate_limit.reset()
    from app.routes.auth import _attempts
    _attempts.clear()
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def new_user(client):
    def make(name="Mai"):
        email = f"{uuid.uuid4().hex[:10]}@test.com"
        r = client.post("/auth/register", json={"name": name, "email": email, "password": "Secret123", "accepted_terms": True})
        assert r.status_code == 200, r.text
        client.headers["Authorization"] = "Bearer " + r.json()["access_token"]
        return r.json()["user"]
    return make

@pytest.fixture
def make_story(client):
    def make(user_id, **overrides):
        from app.database import engine
        from app.models import User
        from app.security import issue
        from sqlmodel import Session
        with Session(engine) as db:
            client.headers["Authorization"] = "Bearer " + issue(db, user_id)
        body = {
            "user_id": user_id, "language": "English", "level": "B1",
            "genre": "Fantasy", "topic": "space", "target_words": 5, "total_chapters": 3,
        }
        body.update(overrides)
        r = client.post("/stories/generate", json=body)
        assert r.status_code == 200, r.text
        return r.json()
    return make
