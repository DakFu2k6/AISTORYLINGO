def build_story_prompt(language: str, level: str, genre: str, topic: str, target_words: int) -> str:
    return f"""
You are an AI language-learning story generator.
Create a short interactive language-learning story.
Learning configuration:
- Language: {language}
- Level: {level}
- Genre: {genre}
- Topic: {topic}
- Target vocabulary: {target_words} words
Requirements:
1. Write the story in the requested language.
2. Match the requested difficulty level.
3. Make the story engaging and easy to understand.
4. Select exactly {target_words} useful vocabulary words.
5. For each vocabulary word provide:
   - word
   - meaning
   - example sentence
6. Return ONLY valid JSON.
JSON structure:
{{
    "title": "Story title",
    "level": "{level}",
    "story": "Story content",
    "vocabulary": [
        {{
            "word": "example",
            "meaning": "meaning",
            "example": "example sentence"
        }}
    ]
}}
"""