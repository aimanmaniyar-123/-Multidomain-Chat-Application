from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models.chat_history import ChatHistory
from datetime import datetime
from backend.schemas.chat import ChatHistorySchema  # ✅ import schema


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/chat-history")
async def save_chat_history(request: Request, db: Session = Depends(get_db)):
    data = await request.json()

    # Extract fields from incoming data
    session_id = data.get("session_id")
    prompt = data.get("prompt")
    response = data.get("response")
    
    # Create new DB object with a real datetime object
    new_entry = ChatHistory(
        session_id=session_id,
        prompt=prompt,
        response=response,
        timestamp=datetime.now()  # ✅ proper datetime
    )

    # Save to DB
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    return {"status": "saved", "id": new_entry.id}


