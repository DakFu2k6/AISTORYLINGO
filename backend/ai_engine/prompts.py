import json
from typing import List, Optional

def _one_line(text: str, limit: int = 120) -> str:
    return " ".join(str(text).split())[:limit]

def build_first_chapter_prompt(
    language: str, level: str, genre: str, topic: str, target_words: int, total_chapters: int
) -> str:
    topic = _one_line(topic)
    return f"""Fast story generator for language learners.
Settings: Language={language}, Level={level}, Genre={genre}, Topic="{topic}", Words={target_words}, Total Chapters={total_chapters}.

Rules:
1. Write Chapter 1 in {language} at level {level}. Keep it short (60-80 words). End with a decision point.
2. Include exactly {target_words} target vocabulary words in the story text.
3. For each word, give: a short English meaning, a short Vietnamese meaning, and ONE short example sentence in {language} (under 8 words). Leave pronunciation and part_of_speech empty "".
4. Give 3 short choices (max 6 words each).
5. Give 1-2 character names and 1 short setting.
6. Return ONLY valid JSON, no markdown formatting.

Format:
{{
  "title": "Short Title",
  "content": "Chapter text...",
  "choices": ["Choice 1", "Choice 2", "Choice 3"],
  "characters": ["Name - role"],
  "setting": "Setting location",
  "vocabulary": [
    {{
      "word": "exact_word",
      "pronunciation": "",
      "part_of_speech": "",
      "meaning": "short english meaning",
      "meaning_vi": "nghĩa tiếng việt ngắn",
      "example": "A short example sentence."
    }}
  ]
}}"""

def build_next_chapter_prompt(
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
    context: Optional[dict] = None,
) -> str:
    if chapter_number >= total_chapters:
        ending_rule = 'FINAL chapter: wrap up story, set "choices": [].'
    else:
        ending_rule = 'End at a choice point. Give 3 short choices (max 6 words).'
    
    words = ", ".join(vocabulary_words[:5])
    return f"""Continue story: "{title}". Language={language}, Level={level}.
Reader chose: "{_one_line(choice, 100)}"
Write Chapter {chapter_number} of {total_chapters}.

Rules:
1. Write 50-70 words in {language}.
2. Reuse at least 1-2 words: {words}.
3. {ending_rule}
4. Return ONLY valid JSON.

Format:
{{
  "content": "Chapter text...",
  "choices": ["Choice 1", "Choice 2", "Choice 3"]
}}"""