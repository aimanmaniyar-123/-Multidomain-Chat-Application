import os
import sys
import uuid
import httpx
import mimetypes
from datetime import datetime
import chainlit as cl

# Add backend path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.memory import store_message
load_dotenv()

# Backend URL from environment
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

#API_BASE = "http://localhost:8000"

# Categories for sidebar
CATEGORIES = [
    {"label": "💬 General", "value": "general"},
    {"label": "💰 Finance", "value": "finance"},
    {"label": "🏡 Real Estate", "value": "real_estate"},
    {"label": "💻 Stocks", "value": "stocks"},
    {"label": "🌤️ Weather", "value": "weather"},
]

# Detect special intents based on user message and category
def detect_intent(message: str, category: str):
    msg = message.lower()
    
    if category == "general":
        if "weather" in msg or "temperature" in msg or "forecast" in msg:
            return "weather"
        elif "stock" in msg or "share" in msg or "ticker" in msg:
            return "stock"
        elif "calendar" in msg or "schedule" in msg or "appointment" in msg:
            return "calendar"
        elif "upload" in msg:
            return "upload"
        else:
            return "chat"
    
    elif category == "finance":
        if any(word in msg for word in ["stock", "share", "ticker", "price", "market"]):
            return "stock"
        elif any(word in msg for word in ["investment", "portfolio", "trading", "finance", "money", "economy", "bank"]):
            return "chat"
        else:
            return "category_mismatch"
    
    elif category == "real_estate":
        if any(word in msg for word in ["property", "house", "apartment", "rent", "buy", "sell", "plot", "land", "real estate", "mortgage", "home"]):
            return "chat"
        else:
            return "category_mismatch"
    
    elif category == "stocks":
        if any(word in msg for word in ["stock", "share", "ticker", "price", "market"]):
            return "stock"
        elif any(word in msg for word in ["trading", "investment", "portfolio", "dividend", "nasdaq", "nyse", "dow"]):
            return "chat"
        else:
            return "category_mismatch"
    
    elif category == "weather":
        if any(word in msg for word in ["weather", "temperature", "forecast", "rain", "sunny", "climate"]):
            return "weather"
        else:
            return "category_mismatch"
    
    return "chat"

# Relevance check
def is_relevant_to_category(message: str, category: str):
    msg = message.lower()
    category_keywords = {
        "finance": ["investment", "portfolio", "trading", "finance", "money", "economy", "bank", "stock", "share", "price", "market", "ticker"],
        "real_estate": ["property", "house", "apartment", "rent", "buy", "sell", "plot", "land", "real estate", "mortgage", "home", "construction", "developer"],
        "stocks": ["stock", "share", "ticker", "price", "market", "trading", "investment", "portfolio", "dividend", "nasdaq", "nyse", "dow"],
        "weather": ["weather", "temperature", "forecast", "rain", "sunny", "climate", "humidity", "wind", "storm", "snow"]
    }
    if category == "general":
        return True
    return any(keyword in msg for keyword in category_keywords.get(category, []))

# Feature toggles from backend
async def get_feature_toggles():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{API_BASE}/admin/feature-toggles")
            if res.status_code == 200:
                return res.json()
            else:
                return {"chat": True, "weather": True, "stock": True, "calendar": True, "upload": True}
    except Exception:
        return {"chat": True, "weather": True, "stock": True, "calendar": True, "upload": True}

@cl.on_chat_start
async def start_chat():
    session_id = str(uuid.uuid4())
    cl.user_session.set("session_id", session_id)
    cl.user_session.set("category", "general")

    await cl.ChatSettings(
        [
            cl.input_widget.Select(
                id="category",
                label="Select Category",
                values=["general", "finance", "real_estate", "stocks", "weather"],
                initial_index=0,
            )
        ]
    ).send()

    await cl.Message(
        content="👋 Welcome! Please choose a domain from the **settings panel** (gear icon in the top right).\n\nYou can also upload PDF or image files for analysis!"
    ).send()

@cl.on_settings_update
async def settings_update(settings):
    selected_category = settings["category"]
    cl.user_session.set("category", selected_category)
    category_labels = {
        "general": "💬 General",
        "finance": "💰 Finance",
        "real_estate": "🏡 Real Estate",
        "stocks": "💻 Stocks",
        "weather": "🌤️ Weather"
    }
    await cl.Message(content=f"✅ Category set to **{category_labels.get(selected_category, selected_category)}**.").send()

@cl.on_message
async def handle_user_message(msg: cl.Message):
    session_id = cl.user_session.get("session_id")
    category = cl.user_session.get("category", "general")
    prompt = msg.content
    reply = ""

    # Get feature toggles
    toggles = await get_feature_toggles()

    # Handle file upload first
    if msg.elements:
        if not toggles.get("upload", True):
            await cl.Message("🚫 File upload is disabled by admin.").send()
            return

        uploaded_file = msg.elements[0]
        file_path = uploaded_file.path
        file_type, _ = mimetypes.guess_type(file_path)

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:  # Increased timeout for file processing
                with open(file_path, "rb") as f:
                    files = {"file": (uploaded_file.name, f, file_type or "application/octet-stream")}
                    
                    # Show processing message
                    processing_msg = await cl.Message(content="⏳ Processing your file...").send()
                    
                    res = await client.post(f"{API_BASE}/upload-file", files=files)

                # Remove processing message
                await processing_msg.remove()

                if res.status_code == 200:
                    data = res.json()
                    
                    if "error" in data:
                        reply = f"❌ {data['error']}"
                    else:
                        file_type_display = data.get("type", "unknown").upper()
                        content = data.get("content", "No content extracted")
                        extracted_text = data.get("extracted_text", "")
                        
                        reply = f"📄 **File:** {uploaded_file.name}\n**Type:** {file_type_display}\n\n**Summary:**\n{content}"
                        
                        # If there's extracted text and it's different from summary, show a preview
                        if extracted_text and extracted_text != content:
                            preview = extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
                            reply += f"\n\n**Extracted Text Preview:**\n```\n{preview}\n```"
                else:
                    reply = f"❌ Upload failed with status {res.status_code}: {res.text}"

        except httpx.TimeoutException:
            reply = "⏰ File processing timed out. Please try with a smaller file."
        except httpx.ConnectError:
            reply = "🔌 Could not connect to backend server."
        except Exception as e:
            reply = f"❌ File upload failed: {str(e)}"

        # Store the interaction
        try:
            store_message(session_id, "user", f"[FILE UPLOAD] {uploaded_file.name}")
            store_message(session_id, "assistant", reply)
        except Exception:
            pass

        await cl.Message(content=reply).send()
        return

    # Check relevance for non-general categories
    if not is_relevant_to_category(prompt, category) and category != "general":
        category_names = {
            "finance": "💰 Finance",
            "real_estate": "🏡 Real Estate", 
            "stocks": "💻 Stocks",
            "weather": "🌤️ Weather"
        }
        await cl.Message(
            content=f"❌ This question doesn't seem related to **{category_names.get(category, category)}**. Please switch to General category or ask a {category}-related question."
        ).send()
        return

    # Detect intent
    intent = detect_intent(prompt, category)
    if intent == "category_mismatch":
        await cl.Message(content="❌ This question doesn't match the selected category.").send()
        return

    # Handle different intents
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get category-specific prompt template
            final_prompt = prompt
            if category != "general":
                try:
                    cat_prompt_res = await client.get(f"{API_BASE}/categories/{category}")
                    if cat_prompt_res.status_code == 200:
                        category_data = cat_prompt_res.json()
                        prompt_template = category_data.get("prompt_template", "")
                        if prompt_template:
                            final_prompt = f"{prompt_template}\n\nUser question: {prompt}"
                except Exception:
                    # If category endpoint fails, continue with original prompt
                    pass

            # Route to appropriate endpoint based on intent
            if intent == "weather":
                if not toggles.get("weather", True):
                    await cl.Message("🚫 Weather feature is disabled by admin.").send()
                    return
                    
                # Extract city from prompt
                city = "london"  # default
                if "in" in prompt:
                    city = prompt.split("in")[-1].strip().replace("?", "").replace(".", "")
                elif "for" in prompt:
                    city = prompt.split("for")[-1].strip().replace("?", "").replace(".", "")
                
                res = await client.get(f"{API_BASE}/weather", params={"city": city})

            elif intent == "stock":
                if not toggles.get("stock", True):
                    await cl.Message("🚫 Stock feature is disabled by admin.").send()
                    return
                    
                # Extract stock symbol from prompt
                words = prompt.upper().split()
                symbol = "AAPL"  # default
                for word in reversed(words):
                    if word.replace("?", "").replace(".", "").isalpha() and len(word) <= 5:
                        symbol = word.replace("?", "").replace(".", "")
                        break
                
                res = await client.get(f"{API_BASE}/stock", params={"symbol": symbol})

            elif intent == "calendar":
                if not toggles.get("calendar", True):
                    await cl.Message("🚫 Calendar feature is disabled by admin.").send()
                    return
                    
                res = await client.get(f"{API_BASE}/calendar-events")

            else:  # Default to chat
                if not toggles.get("chat", True):
                    await cl.Message("🚫 Chat feature is disabled by admin.").send()
                    return
                    
                res = await client.get(f"{API_BASE}/chat", params={"prompt": final_prompt})

            # Parse response
            if res.status_code == 200:
                try:
                    data = res.json()
                    reply = data.get("response") or data.get("result") or str(data)
                    
                    # Clean up common API response artifacts
                    if reply.startswith('{"') and reply.endswith('"}'):
                        try:
                            import json
                            parsed = json.loads(reply)
                            reply = parsed.get("response", reply)
                        except:
                            pass
                            
                except Exception:
                    reply = "⚠️ Could not parse response from backend."
            else:
                reply = f"❌ Backend returned status {res.status_code}: {res.text}"

    except httpx.TimeoutException:
        reply = "⏰ Request timed out. Please try again."
    except httpx.ConnectError:
        reply = "🔌 Could not connect to backend server. Please ensure it's running."
    except Exception as e:
        reply = f"❌ Backend call failed: {str(e)}"

    # Store conversation in memory
    try:
        store_message(session_id, "user", prompt)
        store_message(session_id, "assistant", reply)
        
        # Store in backend chat history
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(f"{API_BASE}/chat-history", json={
                "session_id": session_id,
                "prompt": prompt,
                "response": reply,
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "intent": intent
            })
    except Exception:
        # Don't fail the main response if storage fails
        pass

    await cl.Message(content=reply).send()
