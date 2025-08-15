# Simple in-memory session memory (can be replaced with Redis)
session_memory = {}

def store_message(session_id: str, role: str, content: str):
    if session_id not in session_memory:
        session_memory[session_id] = []
    session_memory[session_id].append({"role": role, "content": content})
