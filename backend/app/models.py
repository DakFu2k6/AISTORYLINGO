from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    password_hash: str
    created_at: datetime = Field(default_factory=utc_now)


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


class QuizResult(SQLModel, table=True):
    __tablename__ = "quiz_results"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    vocabulary_id: int = Field(foreign_key="vocabulary.id")
    story_id: int = Field(foreign_key="stories.id")
    answer: str
    is_correct: bool
    created_at: datetime = Field(default_factory=utc_now)
