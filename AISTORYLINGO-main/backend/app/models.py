from typing import Optional
from sqlmodel import Field, SQLModel  # type: ignore[import-not-found]
from datetime import datetime, timezone

# --- BẢNG USERS ---
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(primary_key=True) # ID lấy từ Firebase
    name: str
    email: str = Field(unique=True, index=True)
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserPreference(SQLModel, table=True):
    __tablename__ = "user_preferences"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    language: str
    level: str
    interests: str 
    learning_goals: str
    target_vocabulary: int

# --- BẢNG STORY ---
class Story(SQLModel, table=True):
    __tablename__ = "stories"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    title: str
    description: Optional[str] = None
    genre: str
    topic: Optional[str] = None
    language: str
    level: str
    status: str = Field(default="in_progress")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Chapter(SQLModel, table=True):
    __tablename__ = "chapters"
    id: Optional[int] = Field(default=None, primary_key=True)
    story_id: int = Field(foreign_key="stories.id")
    chapter_number: int
    content: str
    image_url: Optional[str] = None

class Choice(SQLModel, table=True):
    __tablename__ = "choices"
    id: Optional[int] = Field(default=None, primary_key=True)
    chapter_id: int = Field(foreign_key="chapters.id")
    choice_text: str
    next_chapter_id: Optional[int] = Field(default=None, foreign_key="chapters.id")

# --- BẢNG TỪ VỰNG ---
class Vocabulary(SQLModel, table=True):
    __tablename__ = "vocabulary"
    id: Optional[int] = Field(default=None, primary_key=True)
    word: str = Field(index=True)
    meaning: str
    pronunciation: Optional[str] = None
    example: Optional[str] = None
    difficulty: Optional[str] = None
    story_id: Optional[int] = Field(default=None, foreign_key="stories.id")

class UserVocabulary(SQLModel, table=True):
    __tablename__ = "user_vocabulary"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    vocabulary_id: int = Field(foreign_key="vocabulary.id")
    mastery_level: int = Field(default=0)
    times_reviewed: int = Field(default=0)
    correct_answers: int = Field(default=0)

# --- BẢNG QUIZ ---
class Quiz(SQLModel, table=True):
    __tablename__ = "quiz"
    id: Optional[int] = Field(default=None, primary_key=True)
    chapter_id: int = Field(foreign_key="chapters.id")
    question: str
    options: str # Chuỗi JSON chứa 4 đáp án A B C D
    correct_answer: str

class QuizResult(SQLModel, table=True):
    __tablename__ = "quiz_results"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    quiz_id: int = Field(foreign_key="quiz.id")
    answer: str
    is_correct: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))