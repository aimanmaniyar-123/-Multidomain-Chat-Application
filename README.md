# -Multidomain-Chat-Application
Development of an intelligent chat application with multi-domain categorization, advanced  file processing capabilities, and administrative controls.This project is an AI chatbot platform powered by **Chainlit** (frontend) and **FastAPI** (backend) with:
- **Category-based chat** (weather,Finance, Real Estate, Stocks, General)
- **File upload** (PDF/Image) with OCR + summarization
- **Admin feature toggles & feedback system**
- **Session-based memory** across chats

---

## 🚀 Features
- 📂 Upload **PDF** → Extract text & summarize  
- 🖼 Upload **Images** → OCR text extraction  
- 🌦 Weather info by city  
- 📈 Stock market info by symbol  
- 🗂 Category-specific context in chatbot  
- ⚙ Admin dashboard (feature toggles, feedback logs)  
- 💾 Chat history saved

---

## 🛠 Tech Stack
- **Python 3.10+**
- **FastAPI** – Backend API  
- **Chainlit** – Interactive chatbot frontend  
- **Groq / OpenAI API** – LLM responses  
- **Pytesseract** – OCR for images  
- **pdfminer.six** – PDF text extraction  

---

## 📦 Installation

### 1️⃣ Clone Repository
```bash
git clone https://github.com/aimanmaniyar-123/-Multidomain-Chat-Application
cd -Multidomain-Chat-Application

2️⃣ Create Virtual Environment
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Setup Environment Variables

Copy .env.example to .env and update API keys:

cp .env.example .env       # Mac/Linux
copy .env.example .env     # Windows

🖥 Run Locally
Start FastAPI Backend
uvicorn main:app --reload --port 8000

Start Chainlit Frontend
cd chainlit
chainlit run app.py -w

### License
MIT license

### Contributing
Pull requests are welcome

### Author
Aiman Maniyar

📂 Folder Structure

