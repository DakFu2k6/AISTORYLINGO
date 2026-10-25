
import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["GEMINI_API_KEY"] = ""

from fastapi.testclient import TestClient  

from app.main import app  

def test_full_learning_flow():
    with TestClient(app) as c:
        # Auth
        r = c.post("/auth/register", json={"name": "Mai", "email": "Mai@Test.com", "password": "secret1"})
        assert r.status_code == 200
        user = r.json()["user"]
        assert user["email"] == "mai@test.com"

        r = c.post("/auth/register", json={"name": "Mai", "email": "mai@test.com", "password": "secret1"})
        assert r.status_code == 400  # duplicate email

        assert c.post("/auth/login", json={"email": "mai@test.com", "password": "wrong"}).status_code == 401
        r = c.post("/auth/login", json={"email": "mai@test.com", "password": "secret1"})
        assert r.status_code == 200 and r.json()["user"]["id"] == user["id"]

        # Generate story 
        r = c.post("/stories/generate", json={
            "user_id": user["id"], "language": "English", "level": "B1",
            "genre": "Fantasy", "topic": "space", "target_words": 5, "total_chapters": 3,
        })
        assert r.status_code == 200
        data = r.json()
        story_id = data["story"]["id"]
        ch1 = data["chapter"]
        assert data["story"]["source"] == "demo"
        assert len(data["vocabulary"]) == 5
        assert len(ch1["choices"]) == 3

        # Unknown user is rejected
        bad = c.post("/stories/generate", json={
            "user_id": "nobody", "language": "English", "level": "B1",
            "genre": "Fantasy", "topic": "space", "target_words": 5,
        })
        assert bad.status_code == 404

        # Choices -> chapters 2 and 3 
        r = c.post(f"/stories/{story_id}/next-chapter", json={"chapter_id": ch1["id"], "choice": ch1["choices"][0]})
        assert r.status_code == 200
        ch2 = r.json()["chapter"]
        assert ch2["chapter_number"] == 2 and len(ch2["choices"]) >= 2

        # Same request again returns the same chapter (no duplicate)
        r = c.post(f"/stories/{story_id}/next-chapter", json={"chapter_id": ch1["id"], "choice": ch1["choices"][0]})
        assert r.json()["chapter"]["id"] == ch2["id"]

        r = c.post(f"/stories/{story_id}/next-chapter", json={"chapter_id": ch2["id"], "choice": ch2["choices"][0]})
        body = r.json()
        assert body["chapter"]["chapter_number"] == 3
        assert body["chapter"]["choices"] == []
        assert body["story"]["status"] == "completed"

        r = c.post(f"/stories/{story_id}/next-chapter", json={"chapter_id": body["chapter"]["id"], "choice": "x"})
        assert r.status_code == 400  # story is finished

        # Read again 
        detail = c.get(f"/stories/{story_id}").json()
        assert len(detail["chapters"]) == 3
        assert detail["chapters"][0]["chosen_choice"] == ch1["choices"][0]
        assert len(c.get(f"/stories/history/{user['id']}").json()["data"]) == 1

        # Save a word 
        vocab_id = data["vocabulary"][0]["id"]
        r = c.post("/vocabulary/save", json={"user_id": user["id"], "vocabulary_id": vocab_id})
        assert r.json()["already_saved"] is False
        r = c.post("/vocabulary/save", json={"user_id": user["id"], "vocabulary_id": vocab_id})
        assert r.json()["already_saved"] is True
        saved = c.get(f"/vocabulary/user/{user['id']}").json()
        assert saved["total_words"] == 1 and saved["data"][0]["vocabulary_id"] == vocab_id

        # Quiz 
        quiz = c.get(f"/quiz/story/{story_id}").json()
        assert quiz["total"] == 5
        for q in quiz["questions"]:
            assert len(q["options"]) == 4 and len(set(q["options"])) == 4

        first, second = quiz["questions"][0], quiz["questions"][1]
        right = c.post("/quiz/submit", json={
            "user_id": user["id"], "vocabulary_id": first["vocabulary_id"], "answer": "nonsense"}).json()
        assert right["is_correct"] is False and right["mastery_level"] == 0

        # Answering correctly: use the answer the server reveals
        ok = c.post("/quiz/submit", json={
            "user_id": user["id"], "vocabulary_id": first["vocabulary_id"],
            "answer": right["correct_answer"]}).json()
        assert ok["is_correct"] is True and ok["mastery_level"] == 20
        c.post("/quiz/submit", json={
            "user_id": user["id"], "vocabulary_id": second["vocabulary_id"], "answer": "nonsense"})

        # Dashboard 
        dash = c.get(f"/dashboard/{user['id']}").json()
        stats = dash["statistics"]
        assert stats["total_stories"] == 1 and stats["completed_stories"] == 1
        assert stats["quiz_total"] == 3
        assert stats["quiz_accuracy"] == 33.3
        assert stats["words_saved"] == 2  
        assert len(dash["stories"]) == 1 and len(dash["words"]) == 2
