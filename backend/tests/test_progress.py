import pytest

from datetime import date
from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine
from app import models  
from app.database import ensure_columns
from app.services import progress

@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_streak_rules(db):
    d = date(2026, 11, 1)
    assert progress.award(db, "u1", 10, on=d).streak_days == 1
    assert progress.award(db, "u1", 10, on=d).streak_days == 1             
    assert progress.award(db, "u1", 10, on=date(2026, 11, 2)).streak_days == 2
    assert progress.award(db, "u1", 10, on=date(2026, 11, 3)).streak_days == 3
    stats = progress.award(db, "u1", 10, on=date(2026, 11, 6))             
    assert stats.streak_days == 1 and stats.xp == 50

def test_level_from_xp():
    assert [progress.level_for(x) for x in (0, 99, 100, 250)] == [1, 1, 2, 3]
    assert progress.stats_dict(None) == {"xp": 0, "level": 1, "streak_days": 0}


def test_level_recommendation():
    good, bad, mixed = [True] * 10, [False] * 8 + [True] * 2, [True] * 7 + [False] * 3
    assert progress.recommend_level("B1", good)["suggested_level"] == "B2"
    assert progress.recommend_level("B1", bad)["suggested_level"] == "A2"
    assert progress.recommend_level("B1", mixed)["suggested_level"] == "B1"
    assert progress.recommend_level("C1", good)["suggested_level"] == "C1"   
    assert progress.recommend_level("A1", bad)["suggested_level"] == "A1"   
    assert progress.recommend_level("B1", [True] * 9) is None                
    assert progress.recommend_level(None, good) is None

def test_old_database_gets_the_new_columns():
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE stories (id INTEGER PRIMARY KEY, title TEXT)"))
        conn.execute(text("CREATE TABLE user_vocabulary (id INTEGER PRIMARY KEY, mastery_level INTEGER)"))
        conn.execute(text("INSERT INTO stories (id, title) VALUES (1, 'Old story')"))
    assert sorted(ensure_columns(engine)) == ["stories.context", "user_vocabulary.last_reviewed"]
    assert ensure_columns(engine) == []                                     
    columns = {c["name"] for c in inspect(engine).get_columns("stories")}
    assert "context" in columns
    with engine.begin() as conn:
        assert conn.execute(text("SELECT title FROM stories")).scalar() == "Old story"
