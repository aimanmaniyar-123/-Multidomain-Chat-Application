# main.py

from fastapi import FastAPI, Query, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.llm_provider import get_llm_response
from backend.routes.weather import get_weather
from backend.routes.stocks import get_stock_info
from backend.routes import calendar
from backend.admin_routes import router as admin_router
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pytesseract
from pdfminer.high_level import extract_text
from PIL import Image
import io
import os
import tempfile
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"

app = FastAPI(title="Multi-Domain Chat API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
if os.path.exists("backend/templates"):
    app.mount("/static", StaticFiles(directory="backend/templates"), name="static")
    templates = Jinja2Templates(directory="backend/templates")

# Include routers
app.include_router(admin_router)
app.include_router(calendar.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

# Chat endpoint
@app.get("/chat")
async def chat(prompt: str = Query(..., description="User prompt for chat")):
    try:
        logger.info(f"Chat request: {prompt[:100]}...")
        response = await get_llm_response(prompt)
        return {"response": response}
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

# Weather endpoint
@app.get("/weather")
async def weather(city: str = Query(..., description="City name for weather")):
    try:
        logger.info(f"Weather request for city: {city}")
        result = await get_weather(city)
        return result
    except Exception as e:
        logger.error(f"Weather error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Weather service failed: {str(e)}")

# Stock endpoint
@app.get("/stock")
async def stock(symbol: str = Query(..., description="Stock symbol")):
    try:
        logger.info(f"Stock request for symbol: {symbol}")
        result = await get_stock_info(symbol)
        return result
    except Exception as e:
        logger.error(f"Stock error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stock service failed: {str(e)}")

# Categories endpoint
@app.get("/categories/{category}")
async def get_category_config(category: str):
    """Get category-specific configuration"""
    categories_config = {
        "finance": {
            "name": "Finance",
            "description": "Financial advice and information",
            "prompt_template": "You are a financial advisor. Provide helpful, accurate financial information and advice. Focus on investments, banking, economics, and financial planning."
        },
        "real_estate": {
            "name": "Real Estate",
            "description": "Real estate advice and information",
            "prompt_template": "You are a real estate expert. Provide helpful information about property buying, selling, renting, market trends, and real estate investment."
        },
        "stocks": {
            "name": "Stocks",
            "description": "Stock market information and analysis",
            "prompt_template": "You are a stock market analyst. Provide information about stocks, market trends, trading strategies, and investment analysis. Always mention that this is not financial advice."
        },
        "weather": {
            "name": "Weather",
            "description": "Weather information and forecasts",
            "prompt_template": "You are a weather expert. Provide accurate weather information, forecasts, and climate-related advice."
        }
    }
    
    if category not in categories_config:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return categories_config[category]

# File upload endpoint for PDF or Image
@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process PDF or image files
    Supports: PDF, PNG, JPG, JPEG
    """
    try:
        logger.info(f"File upload request: {file.filename}, type: {file.content_type}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_ext = os.path.splitext(file.filename)[-1].lower()
        if file_ext not in [".pdf", ".png", ".jpg", ".jpeg"]:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file type. Please upload PDF, PNG, JPG, or JPEG files"
            )
        
        # Check file size (limit to 10MB)
        file_bytes = await file.read()
        if len(file_bytes) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")
        
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        extracted_text = ""
        file_type = ""

        if file_ext == ".pdf":
            file_type = "pdf"
            # Create temporary file for PDF processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(file_bytes)
                tmp_path = tmp_file.name
            
            try:
                # Extract text from PDF
                extracted_text = extract_text(tmp_path)
                
                if not extracted_text or not extracted_text.strip():
                    raise HTTPException(status_code=400, detail="No text could be extracted from the PDF")
                
                logger.info(f"Extracted {len(extracted_text)} characters from PDF")
                
            except Exception as e:
                logger.error(f"PDF processing error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")
            finally:
                # Clean up temporary file
                try:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                except Exception as e:
                    logger.warning(f"Could not remove temp file: {str(e)}")

        elif file_ext in [".png", ".jpg", ".jpeg"]:
            file_type = "image"
            try:
                # Process image with OCR
                image = Image.open(io.BytesIO(file_bytes))
                
                # Convert to RGB if necessary
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                extracted_text = pytesseract.image_to_string(image)
                
                if not extracted_text or not extracted_text.strip():
                    raise HTTPException(status_code=400, detail="No text could be extracted from the image")
                
                logger.info(f"Extracted {len(extracted_text)} characters from image")
                
            except Exception as e:
                logger.error(f"Image processing error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

        # Limit text length for LLM processing (prevent token limit issues)
        if len(extracted_text) > 15000:
            extracted_text = extracted_text[:15000] + "/n/n[Text truncated due to length...]"

        # Generate summary using LLM
        try:
            summary_prompt = f"""Please provide a clear and concise summary of the following document:

{extracted_text}

Summary:"""
            
            summary = await get_llm_response(summary_prompt)
            
        except Exception as e:
            logger.error(f"LLM summary error: {str(e)}")
            # Fallback: return extracted text if summary fails
            summary = f"Could not generate summary: {str(e)}/n/nExtracted text available below."

        return {
            "type": file_type,
            "filename": file.filename,
            "content": summary,
            "extracted_text": extracted_text,
            "text_length": len(extracted_text),
            "status": "success"
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

# Chat history endpoint
@app.post("/chat-history")
async def store_chat_history(data: Dict[Any, Any]):
    """Store chat history (implement according to your storage needs)"""
    try:
        # Log the chat history (you can implement database storage here)
        logger.info(f"Chat history stored for session: {data.get('session_id')}")
        return {"status": "stored", "session_id": data.get("session_id")}
    except Exception as e:
        logger.error(f"Chat history storage error: {str(e)}")
        return {"status": "failed", "error": str(e)}

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "detail": str(exc)}

@app.exception_handler(500)
async def server_error_handler(request, exc):
    logger.error(f"Server error: {str(exc)}")
    return {"error": "Internal server error", "detail": "Something went wrong"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
