from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from app.database import get_session
from app.models import Story, Chapter, Vocabulary, Choice
from app.services.story_service import StoryService

# Khởi tạo router DUY NHẤT 1 LẦN cho toàn bộ file
router = APIRouter(prefix="/stories", tags=["Hệ Thống Truyện (Stories)"])

# 1. Khai báo form dữ liệu Frontend gửi lên khi bấm "Generate Story"
class GenerateStoryRequest(BaseModel):
    user_id: str
    language: str
    level: str
    genre: str
    topic: str
    target_words: int = 5

# ==========================================
# API 1: Tạo truyện bằng AI
# ==========================================
@router.post("/generate")
def generate_and_save_story(request: GenerateStoryRequest, db: Session = Depends(get_session)):
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
    db.refresh(new_story)
    
    # BƯỚC 3: Lưu nội dung truyện vào bảng Chapter (Mặc định đây là Chương 1)
    new_chapter = Chapter(
        story_id=new_story.id,
        chapter_number=1,
        content=ai_response.story
    )
    db.add(new_chapter)
    
    # BƯỚC 4: Lưu các từ vựng AI vừa tạo vào Database và lấy ID
    saved_vocabs = []
    for vocab in ai_response.vocabulary:
        new_vocab = Vocabulary(
            word=vocab.word,
            meaning=vocab.meaning,
            example=vocab.example,
            story_id=new_story.id  # <--- Báo cho Database biết từ này thuộc về truyện vừa tạo
        )
        db.add(new_vocab)
        saved_vocabs.append(new_vocab)
        
    # Commit 1 LẦN DUY NHẤT sau khi vòng lặp kết thúc
    db.commit() 
    
    # Refresh lại danh sách để Database cấp ID cho từng từ
    for v in saved_vocabs:
        db.refresh(v)
        
    # BƯỚC 5: Gói gọn dữ liệu trả về cho Frontend hiển thị
    return {
        "message": "AI đã tạo và lưu truyện thành công!",
        "story_id": new_story.id,
        "title": new_story.title,
        "chapter_content": new_chapter.content,
        "vocabulary": saved_vocabs
    }

# ==========================================
# Khai báo form cho việc tạo chương tiếp theo
# ==========================================
class ChoiceRequest(BaseModel):
    chapter_id: int
    choice_text: str
    chapter_number: int

# ==========================================
# API 2: Xử lý rẽ nhánh (Tạo chương tiếp theo)
# ==========================================
@router.post("/{story_id}/next-chapter")
def make_choice_and_continue(story_id: int, request: ChoiceRequest, db: Session = Depends(get_session)):
    old_chapter = db.get(Chapter, request.chapter_id)
    if not old_chapter:
        raise HTTPException(status_code=404, detail="Không tìm thấy chương truyện này trong cơ sở dữ liệu!")

    user_choice = Choice(
        chapter_id=old_chapter.id,
        choice_text=request.choice_text
    )
    db.add(user_choice)
    db.commit()
    db.refresh(user_choice)

    ai_service = StoryService()
    new_story_content = ai_service.generate_next_chapter(
        previous_content=old_chapter.content,
        user_choice=request.choice_text
    )

    new_chapter = Chapter(
        story_id=story_id,
        chapter_number=request.chapter_number,
        content=new_story_content
    )
    db.add(new_chapter)
    db.commit()
    db.refresh(new_chapter)

    user_choice.next_chapter_id = new_chapter.id
    db.commit()

    return {
        "message": "Đã viết xong chương tiếp theo!",
        "new_chapter_id": new_chapter.id,
        "content": new_chapter.content
    }
    
# ==========================================
# API 3: Lấy lịch sử truyện của User
# ==========================================
@router.get("/history/{user_id}")
def get_story_history(user_id: str, db: Session = Depends(get_session)):
    statement = select(Story).where(Story.user_id == user_id).order_by(Story.created_at.desc())
    stories = db.exec(statement).all()
    
    if not stories:
        return {"message": "Chưa có câu chuyện nào.", "data": []}
    return {"data": stories}

# API 4: Lấy chi tiết một câu truyện để đọc lại
@router.get("/{story_id}")
def get_story_details(story_id: int, db: Session = Depends(get_session)):
    story = db.get(Story, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Không tìm thấy truyện này")

    # Kéo các chương truyện
    statement_chapters = select(Chapter).where(Chapter.story_id == story_id).order_by(Chapter.chapter_number)
    chapters = db.exec(statement_chapters).all()
    full_content = "\n\n".join([f"Chương {c.chapter_number}:\n{c.content}" for c in chapters])

    # Kéo từ vựng ĐÃ ĐƯỢC GẮN VỚI TRUYỆN NÀY
    statement_vocabs = select(Vocabulary).where(Vocabulary.story_id == story_id)
    vocabs = db.exec(statement_vocabs).all()

    return {
        "title": story.title,
        "language": story.language,
        "level": story.level,
        "genre": story.genre,
        "topic": story.topic or "N/A",
        "content": full_content,
        "vocabulary": vocabs # <--- Trả về danh sách từ vựng thật
    }