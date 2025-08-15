from pydantic import BaseModel
from datetime import datetime

class ChatHistorySchema(BaseModel):
    session_id: str
    prompt: str
    response: str
    timestamp: datetime
