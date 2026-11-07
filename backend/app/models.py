from datetime import date, datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    role: str = "user"
    google_sub: Optional[str] = Field(default=None, unique=True, index=True)
    password_hash: str
    created_at: datetime = Field(default_factory=utc_now)


class UserStats(SQLModel, table=True):
    __tablename__ = "user_stats"
    user_id: str = Field(foreign_key="users.id", primary_key=True)
    xp: int = 0
    streak_days: int = 0
    last_active: Optional[date] = None

class Story(SQLModel, table=True):
    __tablename__ = "stories"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    title: str
    language: str
    level: str
    genre: str
    topic: str
    total_chapters: int = 3
    status: str = "in_progress"
    source: str = "gemini"
    context: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)

class Chapter(SQLModel, table=True):
    __tablename__ = "chapters"
    id: Optional[int] = Field(default=None, primary_key=True)
    story_id: int = Field(foreign_key="stories.id", index=True)
    chapter_number: int
    content: str
    choices: str = "[]"
    chosen_choice: Optional[str] = None

class Vocabulary(SQLModel, table=True):
    __tablename__ = "vocabulary"
    id: Optional[int] = Field(default=None, primary_key=True)
    story_id: int = Field(foreign_key="stories.id", index=True)
    word: str
    pronunciation: Optional[str] = None
    part_of_speech: Optional[str] = None
    meaning: str
    meaning_vi: Optional[str] = None
    example: Optional[str] = None

class UserVocabulary(SQLModel, table=True):
    __tablename__ = "user_vocabulary"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    vocabulary_id: int = Field(foreign_key="vocabulary.id")
    mastery_level: int = 0
    times_reviewed: int = 0
    correct_answers: int = 0
    last_reviewed: Optional[datetime] = None

class QuizResult(SQLModel, table=True):
    __tablename__ = "quiz_results"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    vocabulary_id: int = Field(foreign_key="vocabulary.id")
    story_id: int = Field(foreign_key="stories.id")
    answer: str
    is_correct: bool
    created_at: datetime = Field(default_factory=utc_now)

class AuthToken(SQLModel, table=True):
    __tablename__ = "auth_tokens"
    digest: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    purpose: str = "session"
    expires_at: datetime

class GoogleChallenge(SQLModel, table=True):
    __tablename__ = "google_challenges"
    digest: str = Field(primary_key=True)
    expires_at: datetime
