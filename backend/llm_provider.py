import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async def get_llm_response(prompt: str) -> str:
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    data = {
        "model":  "llama3-70b-8192",  # or llama3-70b-8b if you prefer
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=15
        )

        try:
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"]
        except Exception as e:
            print("Groq response parsing error:", e)
            print("Raw Groq response:", response.text)
            return "Error: Groq failed to respond properly."
