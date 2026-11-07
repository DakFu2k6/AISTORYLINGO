from typing import List
from pydantic import BaseModel, Field

class VocabularyItem(BaseModel):
    word: str
    pronunciation: str = ""
    part_of_speech: str = ""
    meaning: str
    meaning_vi: str = ""
    example: str = ""

class FirstChapter(BaseModel):
    characters: List[str] = Field(default_factory=list)
    setting: str = ""
    title: str
    content: str
    choices: List[str]
    vocabulary: List[VocabularyItem]

class NextChapter(BaseModel):
    content: str
    choices: List[str] = Field(default_factory=list)
