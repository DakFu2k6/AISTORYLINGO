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
        try:
            prompt = build_story_prompt(
                language=language,
                level=level,
                genre=genre,
                topic=topic,
                target_words=target_words
            )
            
            # Gọi API thật với model chuẩn ổn định nhất
            response = self.client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )
            
            raw_text = response.text.strip()
            
            # Xóa các ký tự markdown thừa nếu Gemini tự ý bọc JSON lại
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
                
            data = json.loads(raw_text.strip())
            return StoryResponse(**data)
            
        except Exception as e:
            # BẪY LỖI: Bắt mọi lỗi 503, 404, quá tải, đứt mạng...
            print(f"Lỗi API Gemini: {e}. Kích hoạt truyện dự phòng!")
            
            # Trả về dữ liệu giả lập chuẩn cấu trúc để Frontend không bị vỡ và Database vẫn lưu được
            fallback_data = {
                "title": "The Backup Story: Return of the Stargazer",
                "chapter_content": f"This is a fallback story because the AI model is currently resting. You wanted a {genre} story about {topic} at {level} level in {language}. The stardust guardian smiled and handed you a backup book bound in aurora light. Everything is still working perfectly in the database!",
                "vocabulary": [
                    {
                        "word": "fallback",
                        "pronunciation": "/ˈfɔːl.bæk/",
                        "part_of_speech": "noun",
                        "meaning": "A backup plan or alternative.",
                        "meaning_vi": "Kế hoạch dự phòng, phương án thay thế.",
                        "example": "The backend developer implemented a clever fallback."
                    },
                    {
                        "word": "guardian",
                        "pronunciation": "/ˈɡɑː.di.ən/",
                        "part_of_speech": "noun",
                        "meaning": "A defender, protector, or keeper.",
                        "meaning_vi": "Người bảo vệ, vệ sĩ.",
                        "example": "The stardust guardian gave her the book."
                    }
                ]
            }
            return StoryResponse(**fallback_data)

    def generate_next_chapter(self, previous_content: str, user_choice: str) -> str:
        try:
            prompt = f"""
            Bạn là người kể chuyện tương tác. 
            Dưới đây là nội dung chương trước:
            {previous_content}
            
            Người dùng đã chọn hành động tiếp theo là: "{user_choice}"
            
            Hãy viết tiếp chương mới (khoảng 150-200 từ) dựa trên lựa chọn này. 
            Chỉ trả về nội dung câu chuyện, không thêm văn bản thừa.
            """
            response = self.client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Lỗi API Gemini khi tạo chương: {e}")
            return "The AI is currently resting, but your journey will continue soon. Please try making your choice again in a few moments."