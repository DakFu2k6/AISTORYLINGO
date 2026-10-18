from fastapi import APIRouter, Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_session
from app.models import Story, Chapter, Vocabulary
from app.services.story_service import StoryService
from app.models import Choice

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

class ChoiceRequest(BaseModel):
    chapter_id: int
    choice_text: str  # Ví dụ: "Investigate the signal"
    chapter_number: int # Số thứ tự của chương tiếp theo

# 2. API xử lý rẽ nhánh
@router.post("/{story_id}/next-chapter")
def make_choice_and_continue(story_id: int, request: ChoiceRequest, db: Session = Depends(get_session)):
    """
    API xử lý khi người dùng đưa ra quyết định để đi tiếp cốt truyện.
    """
    # Bước 1: Lấy nội dung chương cũ từ Database để AI biết bối cảnh
    old_chapter = db.get(Chapter, request.chapter_id)
    if not old_chapter:
        raise HTTPException(status_code=404, detail="Không tìm thấy chương truyện này trong cơ sở dữ liệu!")

    # Bước 2: Lưu sự lựa chọn của người dùng vào bảng 'choices'
    user_choice = Choice(
        chapter_id=old_chapter.id,
        choice_text=request.choice_text
    )
    db.add(user_choice)
    db.commit()
    db.refresh(user_choice)

    # Bước 3: Đưa bối cảnh và lựa chọn cho Gemini viết tiếp chương mới
    ai_service = StoryService()
    new_story_content = ai_service.generate_next_chapter(
        previous_content=old_chapter.content,
        user_choice=request.choice_text
    )

    # Bước 4: Lưu chương mới mà AI vừa viết vào bảng 'chapters'
    new_chapter = Chapter(
        story_id=story_id,
        chapter_number=request.chapter_number,
        content=new_story_content
    )
    db.add(new_chapter)
    db.commit()
    db.refresh(new_chapter)

    # Bước 5: Cập nhật khóa ngoại - Báo cho Database biết lựa chọn cũ dẫn tới chương mới nào
    user_choice.next_chapter_id = new_chapter.id
    db.commit()

    # Trả về kết quả cho Frontend hiển thị chương tiếp theo
    return {
        "message": "Đã viết xong chương tiếp theo!",
        "new_chapter_id": new_chapter.id,
        "content": new_chapter.content
    }