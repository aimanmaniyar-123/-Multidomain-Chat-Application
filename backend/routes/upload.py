from fastapi import APIRouter, UploadFile, File
from PyPDF2 import PdfReader
import pytesseract
from PIL import Image
import io
import re

# Set Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"

router = APIRouter()

def clean_extracted_text(text: str) -> str:
    # Collapse multiple spaces, remove newlines, extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    content = ""

    if file.filename.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(contents))
        for page in reader.pages:  # process all pages
            content += page.extract_text() or ""
    elif file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        image = Image.open(io.BytesIO(contents))
        content = pytesseract.image_to_string(image)
    else:
        return {"error": "Unsupported file type"}

    cleaned = clean_extracted_text(content)

    return {"summary": cleaned}  # ✅ return full cleaned text
