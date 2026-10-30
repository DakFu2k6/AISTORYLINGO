import json
import os
from typing import List, Tuple

from google import genai
from google.genai import types

from ai_engine.prompts import build_first_chapter_prompt, build_next_chapter_prompt
from ai_engine.schemas import FirstChapter, NextChapter
from app.services.demo_story import demo_first_chapter, demo_next_chapter

def _parse_json(text: str) -> dict:
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


class StoryService:
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.client = genai.Client(api_key=api_key) if api_key else None
        self.model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    def _ask_json(self, prompt: str) -> dict:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        return _parse_json(response.text)

    # Chapter 1 
    def first_chapter(
        self, language: str, level: str, genre: str, topic: str, target_words: int, total_chapters: int
    ) -> Tuple[FirstChapter, str]:
        if self.client:
            try:
                prompt = build_first_chapter_prompt(
                    language, level, genre, topic, target_words, total_chapters
                )
                data = FirstChapter(**self._ask_json(prompt))
                data.vocabulary = data.vocabulary[:target_words]
                data.choices = [c for c in data.choices if c.strip()][:3]
                if not data.content.strip() or not data.vocabulary or len(data.choices) < 2:
                    raise ValueError("AI answer is incomplete")
                return data, "gemini"
            except Exception as e:  # network, quota, bad JSON, wrong model name...
                print(f"[Gemini] chapter 1 failed ({e}). Using the demo story instead.")
        return demo_first_chapter(target_words), "demo"

    # Next chapters 
    def next_chapter(
        self,
        title: str,
        language: str,
        level: str,
        genre: str,
        topic: str,
        previous_chapters: List[str],
        choice: str,
        chapter_number: int,
        total_chapters: int,
        vocabulary_words: List[str],
    ) -> Tuple[NextChapter, str]:
        is_last = chapter_number >= total_chapters
        if self.client:
            try:
                prompt = build_next_chapter_prompt(
                    title, language, level, genre, topic, previous_chapters,
                    choice, chapter_number, total_chapters, vocabulary_words,
                )
                data = NextChapter(**self._ask_json(prompt))
                data.choices = [] if is_last else [c for c in data.choices if c.strip()][:3]
                if not data.content.strip() or (not is_last and len(data.choices) < 2):
                    raise ValueError("AI answer is incomplete")
                return data, "gemini"
            except Exception as e:
                print(f"[Gemini] chapter {chapter_number} failed ({e}). Using demo text instead.")
        return demo_next_chapter(choice, chapter_number, total_chapters), "demo"
