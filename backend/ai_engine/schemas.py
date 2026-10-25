from typing import List
from pydantic import BaseModel

class VocabularyItem(BaseModel):
    word: str
    pronunciation: str = ""
    part_of_speech: str = ""
    meaning: str
    meaning_vi: str = ""
    example: str = ""

class FirstChapter(BaseModel):
    title: str
    content: str
    choices: List[str]
    vocabulary: List[VocabularyItem]

class NextChapter(BaseModel):
    content: str
    choices: List[str] = []
