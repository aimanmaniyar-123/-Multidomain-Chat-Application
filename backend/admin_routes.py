from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, List
from backend.memory import session_memory
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="backend/templates")

ALL_FEATURES = {
    "chat": True,
    "upload": True,
    "calendar": True,
    "weather": True,
    "stock": True
}
feature_toggles: Dict[str, bool] = ALL_FEATURES.copy()
feedback_store: List[Dict] = []
chat_logs: List[Dict] = []

prompt_categories = {
    "finance": "You are a financial advisor. Answer concisely.",
    "real_estate": "You are a real estate expert. Provide location-specific insights.",
    "tech_support": "You are a tech support assistant. Fix issues clearly."
}

@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "features": feature_toggles,
        "feedbacks": feedback_store,
        "chat_logs": chat_logs[-10:],
    })

@router.get("/admin/feature-toggles")
def get_feature_toggles():
    return feature_toggles

@router.post("/admin/feature-toggles/{feature}/{state}")
def toggle_feature(feature: str, state: str):
    if feature not in ALL_FEATURES:
        raise HTTPException(status_code=404, detail="Feature not found")
    feature_toggles[feature] = state.lower() == "true"
    return {"message": f"{feature} feature set to {state.lower()}"}

class Feedback(BaseModel):
    session_id: str
    prompt: str
    response: str
    note: str

@router.post("/feedback")
def submit_feedback(feedback: Feedback):
    feedback_store.append(feedback.dict())
    return {"message": "Feedback submitted"}

@router.get("/feedbacks")
def get_feedbacks():
    return feedback_store

@router.get("/categories")
def list_categories():
    return list(prompt_categories.keys())

@router.get("/categories/{category}")
def get_prompt_template(category: str):
    if category not in prompt_categories:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"category": category, "prompt_template": prompt_categories[category]}

@router.post("/admin/log-chat")
def log_chat(session_id: str, prompt: str, response: str):
    chat_logs.append({
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "prompt": prompt,
        "response": response
    })
    return {"message": "Chat logged"}

@router.get("/memory/{session_id}")
def get_memory(session_id: str):
    return session_memory.get(session_id, [])
