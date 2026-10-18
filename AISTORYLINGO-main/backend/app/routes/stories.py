from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_session
from app.models import Story, Chapter, Vocabulary
# Gọi cái service Gemini mà bạn đã cấu hình trước đó
from app.services.story_service import StoryService

# Tạo router cho toàn bộ tính năng liên quan đến Truyện
router = APIRouter(prefix="/stories", tags=["Hệ Thống Truyện (Stories)"])

# 1. Khai báo form dữ liệu Frontend gửi lên khi bấm "Generate Story"
class GenerateStoryRequest(BaseModel):
    user_id: str
    language: str
    level: str
    genre: str
    topic: str
    target_words: int = 5

# 2. API chính: Tạo truyện bằng AI và lưu thẳng vào Database
@router.post("/generate")
def generate_and_save_story(request: GenerateStoryRequest, db: Session = Depends(get_session)):
    """
    API này làm 4 việc rõ ràng:
    1. Gọi Gemini API tạo truyện.
    2. Lưu tên truyện vào bảng 'stories'.
    3. Lưu nội dung vào bảng 'chapters'.
    4. Lưu danh sách từ vựng vào bảng 'vocabulary'.
    """
    
    # BƯỚC 1: Đưa thông tin cho Gemini AI viết truyện
    ai_service = StoryService()
    ai_response = ai_service.generate_story(
        language=request.language,
        level=request.level,
        genre=request.genre,
        topic=request.topic,
        target_words=request.target_words
    )
    
    # BƯỚC 2: Lưu thông tin chung của truyện vào Database
    new_story = Story(
        user_id=request.user_id,
        title=ai_response.title,
        genre=request.genre,
        language=request.language,
        level=request.level,
        status="in_progress"
    )
    db.add(new_story)
    db.commit()
    db.refresh(new_story) # Refresh để lấy được ID của truyện vừa tạo
    
    # BƯỚC 3: Lưu nội dung truyện vào bảng Chapter (Mặc định đây là Chương 1)
    new_chapter = Chapter(
        story_id=new_story.id,
        chapter_number=1,
        content=ai_response.story # .story này là field trả về từ AI Schema của bạn
    )
    db.add(new_chapter)
    
    # BƯỚC 4: Lưu các từ vựng AI vừa tạo vào Database
    for vocab in ai_response.vocabulary:
        new_vocab = Vocabulary(
            word=vocab.word,
            meaning=vocab.meaning,
            example=vocab.example
        )
        db.add(new_vocab)
        
    # Lưu toàn bộ Chapter và Vocabulary vào CSDL trong 1 lần duy nhất
    db.commit()
    
    # BƯỚC 5: Gói gọn dữ liệu trả về cho Frontend hiển thị
    return {
        "message": "AI đã tạo và lưu truyện thành công!",
        "story_id": new_story.id,
        "title": new_story.title,
        "chapter_content": new_chapter.content,
        "vocabulary": ai_response.vocabulary
    }