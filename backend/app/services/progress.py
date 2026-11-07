from datetime import date, datetime, timedelta, timezone
from typing import Optional, Sequence
from sqlmodel import Session
from app.models import UserStats

XP_CORRECT = 10
XP_WRONG = 2            
XP_STORY_COMPLETED = 30
XP_PER_LEVEL = 100

LEVELS = ["A1", "A2", "B1", "B2", "C1"]
MIN_ANSWERS_FOR_ADVICE = 10
MOVE_UP_AT = 0.90
MOVE_DOWN_BELOW = 0.45

def today() -> date:
    return datetime.now(timezone.utc).date()

def level_for(xp: int) -> int:
    return xp // XP_PER_LEVEL + 1

def award(db: Session, user_id: str, xp: int, on: Optional[date] = None) -> UserStats:
    on = on or today()
    stats = db.get(UserStats, user_id) or UserStats(user_id=user_id)
    if stats.last_active == on:
        pass                                        
    elif stats.last_active == on - timedelta(days=1):
        stats.streak_days += 1                      
    else:
        stats.streak_days = 1                       
    stats.last_active = on
    stats.xp += xp
    db.add(stats)
    return stats

def stats_dict(stats: Optional[UserStats]) -> dict:
    xp = stats.xp if stats else 0
    return {
        "xp": xp,
        "level": level_for(xp),
        "streak_days": stats.streak_days if stats else 0,
    }

def recommend_level(current_level: Optional[str], recent_correct: Sequence[bool]) -> Optional[dict]:
    if current_level not in LEVELS or len(recent_correct) < MIN_ANSWERS_FOR_ADVICE:
        return None
    accuracy = sum(recent_correct) / len(recent_correct)
    index = LEVELS.index(current_level)
    percent = round(accuracy * 100)
    n = len(recent_correct)
    if accuracy >= MOVE_UP_AT and index < len(LEVELS) - 1:
        suggested = LEVELS[index + 1]
        message = f"You got {percent}% of your last {n} answers right. Ready to try level {suggested}?"
    elif accuracy < MOVE_DOWN_BELOW and index > 0:
        suggested = LEVELS[index - 1]
        message = f"You got {percent}% of your last {n} answers right. Level {suggested} may feel more comfortable for now."
    else:
        suggested = current_level
        message = f"You got {percent}% of your last {n} answers right. Level {current_level} fits you well."
    return {"current_level": current_level, "suggested_level": suggested, "accuracy": percent, "message": message}
