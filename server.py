
import os
import time
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

# .env faylidan API kalitlarini o'qish
load_dotenv(Path(__file__).with_name(".env"))

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        ".env faylida GEMINI_API_KEY topilmadi."
    )

client = genai.Client(
    api_key=API_KEY,
    http_options={"timeout": 20000}
)
MODEL = "gemini-3.5-flash-lite"

app = FastAPI(title="Advisor AI API")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return {"status": "ok", "message": "Advisor AI server ishlayapti"}

@limiter.limit("10/minute")
@app.post("/chat")
def chat(request: ChatRequest):
    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Savol bo'sh bo'lmasligi kerak."
        )

    if len(message) > 2000:
        raise HTTPException(
            status_code=400,
            detail="Savol 2000 belgidan oshmasin."
        )

    
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=(
                "Sen Advisor AI nomli professional biznes yordamchisisan. "
                "O'zbek tilida sodda, aniq va amaliy javob ber. "
                "Javoblarda mos emojilardan foydalan: 💡 g'oya, "
                "💰 budjet, 📊 hisob-kitob, ⚠️ xavf, 🚀 keyingi qadam. "
                "Kerak bo'lsa sarlavha va punktlardan foydalan. "
                "Emojilarni me'yorida ishlat, har bir gapga qo'shma. "
                "Budjet, xarajatlar va bozor talabini hisobga ol. "
                "Daromadni kafolatlama. "
                "Foydalanuvchining savoli: " + message
            ),
        )

        answer = response.text or "Hozir javob tayyorlay olmadim."
        return {"reply": answer}

    except Exception as error:
        print("Gemini xatosi:", type(error).__name__, str(error))
        raise HTTPException(
            status_code=503,
            detail="AI hozir javob bera olmadi. Keyinroq qayta urinib ko'ring."
        )

