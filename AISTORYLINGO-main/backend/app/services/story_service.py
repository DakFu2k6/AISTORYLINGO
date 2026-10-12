import os
import json

from google import genai
from ai_engine.prompts.story_prompt import build_story_prompt
from ai_engine.schemas.story_schema import StoryResponse

class StoryService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured")
        self.client = genai.Client(api_key=api_key)

    def generate_story(self, language: str, level: str, genre: str, topic: str, target_words: int) -> StoryResponse:
        prompt = build_story_prompt(
            language=language,
            level=level,
            genre=genre,
            topic=topic,
            target_words=target_words
        )
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        raw_text = response.text
        data = json.loads(raw_text)
        return StoryResponse(**data)