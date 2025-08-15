from fastapi import APIRouter, Query
from backend.llm_provider import get_llm_response

router = APIRouter()

@router.get("/chat")
def chat(prompt: str = Query(...)):
    reply = get_llm_response(prompt)
    return {"response": reply}
