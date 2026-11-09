from __future__ import annotations

import json
import logging
import math
import os
import re
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable, List, Optional, Type
from google import genai
from google.genai import types
from pydantic import BaseModel
from ai_engine.prompts import build_first_chapter_prompt, build_next_chapter_prompt
from ai_engine.schemas import FirstChapter, NextChapter
from app.services.demo_story import demo_first_chapter, demo_next_chapter

log = logging.getLogger("storylingo.ai")

# 1. Cố định luôn model nhanh nhất tại đây, bỏ qua cấu hình trong file .env
DEFAULT_MODEL = "gemini-flash-latest"
NO_KEY_REASON = "No GEMINI_API_KEY was loaded. Put it in the project .env file and restart the server."

@dataclass
class AIResult:
    data: Any                              
    source: str                            
    fallback_reason: Optional[str] = None  

def _parse_json(text: str) -> dict:
    text = (text or "").strip()
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.S | re.I)
    if fenced:
        text = fenced.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise

_LATIN = re.compile(r"[A-Za-zÀ-ɏ'’\- ]+")

def word_in_text(word: str, text: str) -> bool:
    word = word.strip()
    if not word:
        return False
    if _LATIN.fullmatch(word):
        return re.search(rf"(?<!\w){re.escape(word)}(?!\w)", text, re.I) is not None
    return word in text

def _validate_first(data: FirstChapter, target_words: int) -> FirstChapter:
    data.choices = [c.strip() for c in data.choices if c.strip()][:3]
    if not data.content.strip():
        raise ValueError("the chapter text is empty")
    if len(data.choices) < 2:
        raise ValueError("fewer than 2 choices")
    seen, valid = set(), []
    for item in data.vocabulary:
        key = item.word.strip().lower()
        if key and key not in seen and item.meaning.strip() and word_in_text(item.word, data.content):
            seen.add(key)
            valid.append(item)
    needed = max(1, math.ceil(target_words / 2))
    if len(valid) < needed:
        raise ValueError(f"only {len(valid)} of {target_words} vocabulary words appear in the chapter text")
    data.vocabulary = valid[:target_words]
    data.characters = [c.strip() for c in data.characters if c.strip()][:3]
    return data

def _validator_next(is_last: bool) -> Callable[[NextChapter], None]:
    def check(data: NextChapter) -> None:
        data.choices = [] if is_last else [c.strip() for c in data.choices if c.strip()][:3]
        if not data.content.strip():
            raise ValueError("the chapter text is empty")
        if not is_last and len(data.choices) < 2:
            raise ValueError("fewer than 2 choices")
    return check

class StoryService:
    def __init__(self, client: Any = None, model: Optional[str] = None) -> None:
        self.model = (model or DEFAULT_MODEL).strip()
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.backend = "none"          
        self.client: Any = None
        self.last_error: Optional[str] = None
        self.init_note: Optional[str] = None
        self._probe_cache: Optional[tuple[float, dict]] = None
        
        if client is not None:
            self.client, self.backend = client, "custom"
        elif self.api_key:
            try:
                self.client, self.backend = self._make_client()
            except Exception as exc:  
                self.init_note = self._explain(exc)
                self.last_error = self.init_note
                log.error("Could not create the Gemini client: %s", self.init_note)
        else:
            self.init_note = NO_KEY_REASON

    def _make_client(self) -> tuple[Any, str]:
        timeout_ms = int(float(os.getenv("GEMINI_TIMEOUT_SECONDS", "90")) * 1000)
        api_version = os.getenv("GEMINI_API_VERSION", "v1beta").strip().lower()
        if api_version not in {"v1", "v1beta"}:
            raise ValueError(f"Unsupported Gemini API version: {api_version}")
        http = types.HttpOptions(api_version=api_version, timeout=timeout_ms)
        choice = os.getenv("GEMINI_BACKEND", "auto").strip().lower()
        use_vertex = (choice == "vertex" or (choice == "auto" and self.api_key.startswith("AQ.")))
        if use_vertex:
            return genai.Client(vertexai=True, api_key=self.api_key, http_options=http), "vertex"
        return genai.Client(api_key=self.api_key, http_options=http), "studio"

    @property
    def configured(self) -> bool:
        return self.client is not None

    def describe(self) -> dict:
        return {
            "key_loaded": bool(self.api_key) or self.backend == "custom",
            "configured": self.configured,
            "backend": self.backend,
            "model": self.model,
            "last_error": self.last_error or self.init_note,
        }

    def _redact(self, text: str) -> str:
        return text.replace(self.api_key, "***") if self.api_key else text

    def _explain(self, exc: Exception) -> str:
        code = getattr(exc, "code", None)
        raw = self._redact(str(exc)).strip()
        low = raw.lower()
        if code in (401, 403) or "api key" in low or "api_key" in low or "permission_denied" in low:
            return ("Gemini rejected the API key. Create a new key at aistudio.google.com/apikey. "
                    "Keys starting with 'AQ.' need GEMINI_BACKEND=vertex, keys starting with 'AIza' need GEMINI_BACKEND=studio.")
        if code == 404 or "not_found" in low:
            return f"Model '{self.model}' was not found. Check model settings in story_service.py."
        if code == 429 or "resource_exhausted" in low or "quota" in low:
            return "Gemini quota or rate limit reached. Wait a minute, or use another key or model."
        if code in (500, 502, 503, 504) or "unavailable" in low or "overloaded" in low:
            return "Gemini is overloaded right now. Try again in a moment."
        if "timed out" in low or "timeout" in low:
            return "Gemini took too long to answer (timeout)."
        if isinstance(exc, (ValueError, json.JSONDecodeError)):
            return f"The AI answer was not usable: {raw[:160]}"
        return f"{type(exc).__name__}: {raw[:200]}"

    @staticmethod
    def _is_fatal(exc: Exception) -> bool:
        code = getattr(exc, "code", None)
        low = str(exc).lower()
        return code in (401, 403, 404, 429) or "api key" in low or "api_key" in low

    def _remember(self, exc: Exception) -> str:
        reason = self._explain(exc)
        self.last_error = reason
        log.warning("Gemini call failed, using the demo story. Reason: %s", reason)
        return reason

    def _ask(self, prompt: str, schema: Type[BaseModel], validate: Callable[[Any], Any]) -> Any:
        last_exc: Optional[Exception] = None
        
        # 4. Cơ chế Exponential Backoff: Chờ giãn cách thời gian để né nghẽn mạng chớp nhoáng
        attempts = [
            (True, 0),     # Lần 1: Thử ngay lập tức với schema chuẩn
            (False, 2.0),  # Lần 2: Đợi 2 giây rồi gọi lại, bỏ schema
            (False, 4.0)   # Lần 3: Đợi 4 giây rồi gọi lại lần cuối
        ]

        for use_schema, delay in attempts:
            if delay > 0:
                log.info("-> [RETRY] Dang doi %.1f giay truoc khi thu lai ket noi Gemini...", delay)
                time.sleep(delay)

            try:
                # 2 & 3. Hạ temperature xuống 0.2 và ép max_output_tokens 1024 để tăng tốc độ phản hồi cực hạn
                config: dict = {
                    "response_mime_type": "application/json", 
                    "temperature": 0.2,
                    "max_output_tokens": 1024
                }
                if use_schema:
                    config["response_schema"] = schema
                
                start_time = time.time()
                log.info("-> [DIAGNOSTIC] Dang gui yeu cau toi Gemini (model=%s, schema=%s)...", self.model, use_schema)
                
                response = self.client.models.generate_content(
                    model=self.model, contents=prompt, config=types.GenerateContentConfig(**config)
                )
                
                elapsed = time.time() - start_time
                log.info("<- [DIAGNOSTIC] Gemini phan hoi thanh cong trong %.2f giay.", elapsed)

                parsed = schema(**_parse_json(response.text))
                result = validate(parsed)
                return parsed if result is None else result

            except Exception as exc:
                last_exc = exc
                elapsed = time.time() - start_time if 'start_time' in locals() else 0
                log.info("x [DIAGNOSTIC] Lan goi (schema=%s) that bai sau %.2f giay. Loi: %s", use_schema, elapsed, self._explain(exc))
                
                if self._is_fatal(exc):
                    break
                    
        assert last_exc is not None
        raise last_exc

    def first_chapter(
        self, language: str, level: str, genre: str, topic: str, target_words: int, total_chapters: int
    ) -> AIResult:
        reason = self.init_note
        if self.client:
            try:
                prompt = build_first_chapter_prompt(language, level, genre, topic, target_words, total_chapters)
                data = self._ask(prompt, FirstChapter, lambda d: _validate_first(d, target_words))
                self.last_error = None
                return AIResult(data, "gemini")
            except Exception as exc:
                reason = self._remember(exc)
        return AIResult(demo_first_chapter(target_words), "demo", reason)

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
        context: Optional[dict] = None,
    ) -> AIResult:
        is_last = chapter_number >= total_chapters
        reason = self.init_note
        if self.client:
            try:
                prompt = build_next_chapter_prompt(
                    title, language, level, genre, topic, previous_chapters,
                    choice, chapter_number, total_chapters, vocabulary_words, context,
                )
                data = self._ask(prompt, NextChapter, _validator_next(is_last))
                self.last_error = None
                return AIResult(data, "gemini")
            except Exception as exc:
                reason = self._remember(exc)
        return AIResult(demo_next_chapter(choice, chapter_number, total_chapters), "demo", reason)

    def probe(self) -> dict:
        now = time.monotonic()
        if self._probe_cache and now - self._probe_cache[0] < 30:
            return self._probe_cache[1]
        if not self.client:
            result = {"ok": False, "error": self.init_note or NO_KEY_REASON}
        else:
            try:
                response = self.client.models.generate_content(
                    model=self.model, contents="Reply with the single word: OK"
                )
                result = {"ok": True, "reply": (response.text or "").strip()[:40]}
            except Exception as exc:
                result = {"ok": False, "error": self._explain(exc)}
        self._probe_cache = (now, result)
        return result

@lru_cache(maxsize=1)
def get_story_service() -> StoryService:
    return StoryService()