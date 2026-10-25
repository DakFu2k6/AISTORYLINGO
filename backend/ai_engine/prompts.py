from typing import List

def build_first_chapter_prompt(
    language: str, level: str, genre: str, topic: str, target_words: int, total_chapters: int
) -> str:
    return f"""You are a language-learning story writer.
Write CHAPTER 1 of an interactive story with {total_chapters} chapters in total.

Learner settings:
- Language to learn: {language}
- Level (CEFR): {level}
- Genre: {genre}
- Topic: {topic}
- Number of vocabulary words: {target_words}

Rules:
1. Write the story in {language}, with vocabulary and grammar suitable for level {level}.
2. Chapter 1 is 100-140 words and ends at a moment where the reader must decide what to do.
3. Pick exactly {target_words} useful vocabulary words. Each word MUST appear in the chapter text, spelled exactly as written there.
4. For each word give: pronunciation (IPA or romanization), part_of_speech, meaning (simple English), meaning_vi (Vietnamese) and example (a NEW sentence in {language}).
5. Give exactly 3 short choices (max 10 words each, written in {language}) for what the reader can do next.
6. Return ONLY valid JSON, with no markdown.

JSON format:
{{
  "title": "Story title",
  "content": "Chapter 1 text",
  "choices": ["choice 1", "choice 2", "choice 3"],
  "vocabulary": [
    {{
      "word": "word",
      "pronunciation": "/.../",
      "part_of_speech": "noun",
      "meaning": "simple English meaning",
      "meaning_vi": "nghia tieng Viet",
      "example": "An example sentence."
    }}
  ]
}}
"""


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
) -> str:
    story_so_far = "\n\n".join(
        f"Chapter {i}:\n{text}" for i, text in enumerate(previous_chapters, start=1)
    )
    if chapter_number >= total_chapters:
        ending_rule = 'This is the FINAL chapter. Bring the story to a satisfying ending and set "choices" to an empty list [].'
    else:
        ending_rule = (
            "End at a moment where the reader must decide what to do. "
            f"Give exactly 3 short choices (max 10 words each, written in {language})."
        )
    words = ", ".join(vocabulary_words)

    return f"""You are a language-learning story writer continuing an interactive story.

Story title: {title}
Language: {language} | Level (CEFR): {level} | Genre: {genre} | Topic: {topic}

Story so far:
{story_so_far}

The reader chose: "{choice}"

Write CHAPTER {chapter_number} of {total_chapters}.
Rules:
1. Write in {language} at level {level}, 80-120 words.
2. Follow the reader's choice and keep the same characters and setting.
3. Reuse at least 2 of these vocabulary words, spelled exactly: {words}
4. {ending_rule}
5. Return ONLY valid JSON, with no markdown.

JSON format:
{{
  "content": "Chapter {chapter_number} text",
  "choices": ["choice 1", "choice 2", "choice 3"]
}}
"""
