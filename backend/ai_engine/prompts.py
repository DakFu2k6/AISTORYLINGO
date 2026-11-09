import json
from typing import List, Optional

def _one_line(text: str, limit: int = 120) -> str:
    return " ".join(str(text).split())[:limit]

def build_first_chapter_prompt(
    language: str, level: str, genre: str, topic: str, target_words: int, total_chapters: int
) -> str:
    topic = _one_line(topic)
    return f"""Story generator for language learners.
Settings: Language={language}, Level={level}, Genre={genre}, Topic="{topic}", Words={target_words}, Total Chapters={total_chapters}.

Rules:
1. Write Chapter 1 in {language} at level {level}. Make it engaging and descriptive (around 100-130 words). End with a clear decision point.
2. Include exactly {target_words} target vocabulary words naturally in the story text.
3. For each target word, provide: pronunciation (IPA), part of speech, a clear English meaning, a Vietnamese meaning, and a natural example sentence in {language}.
4. Give 3 distinct choices (max 8 words each).
5. Give 1-2 character names and a descriptive setting.
6. Return ONLY valid JSON, no markdown formatting.

Format:
{{
  "title": "Story Title",
  "content": "Full chapter text...",
  "choices": ["Choice 1", "Choice 2", "Choice 3"],
  "characters": ["Name - role"],
  "setting": "Setting description",
  "vocabulary": [
    {{
      "word": "exact_word",
      "pronunciation": "/IPA/",
      "part_of_speech": "noun/verb/etc",
      "meaning": "english meaning",
      "meaning_vi": "nghĩa tiếng việt",
      "example": "Example sentence using the word."
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
        ending_rule = 'FINAL chapter: wrap up the story nicely, set "choices": [].'
    else:
        ending_rule = 'End at an exciting choice point. Give 3 short choices (max 8 words).'
    
    words = ", ".join(vocabulary_words[:5])
    return f"""Continue story: "{title}". Language={language}, Level={level}.
Reader chose: "{_one_line(choice, 100)}"
Write Chapter {chapter_number} of {total_chapters}.

Rules:
1. Write 100-120 words in {language}, keeping narrative flow.
2. Reuse at least 2-3 words from: {words}.
3. {ending_rule}
4. Return ONLY valid JSON.

Format:
{{
  "content": "Chapter text...",
  "choices": ["Choice 1", "Choice 2", "Choice 3"]
}}"""