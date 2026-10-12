from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship  # type: ignore[import-not-found]
from datetime import datetime, timezone

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(primary_key=True) # Dùng Firebase UID
    name: str
    email: str = Field(unique=True, index=True)
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

class Story(SQLModel, table=True):
    __tablename__ = "stories"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    title: str
    description: Optional[str] = None
    genre: str
    language: str
    level: str
    status: str = Field(default="in_progress") # in_progress, completed
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

class Vocabulary(SQLModel, table=True):
    __tablename__ = "vocabulary"
    id: Optional[int] = Field(default=None, primary_key=True)
    word: str = Field(index=True)
    meaning: str
    pronunciation: Optional[str] = None
    example: Optional[str] = None
    difficulty: Optional[str] = None

class UserVocabulary(SQLModel, table=True):
    __tablename__ = "user_vocabulary"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    vocabulary_id: int = Field(foreign_key="vocabulary.id")
    mastery_level: int = Field(default=0) # 0 đến 100%
    times_reviewed: int = Field(default=0)
    correct_answers: int = Field(default=0)
    last_reviewed: Optional[datetime] = None


class Quiz(SQLModel, table=True):
    __tablename__ = "quiz"
    id: Optional[int] = Field(default=None, primary_key=True)
    chapter_id: int = Field(foreign_key="chapters.id")
    question: str
    options: str 
    correct_answer: str

class QuizResult(SQLModel, table=True):
    __tablename__ = "quiz_results"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    quiz_id: int = Field(foreign_key="quiz.id")
    answer: str
    is_correct: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))