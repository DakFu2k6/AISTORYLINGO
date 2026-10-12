from pydantic import BaseModel
from typing import List

class VocabularyItem(BaseModel):
    word: str
    meaning: str
    example: str

class StoryResponse(BaseModel):
    title: str
    level: str
    story: str
    vocabulary: List[VocabularyItem]