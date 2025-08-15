from sqlalchemy import Column, Integer, String, DateTime
from backend.database import Base
from datetime import datetime

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    prompt = Column(String)
    response = Column(String)
    timestamp = Column(DateTime, default=datetime.now)
