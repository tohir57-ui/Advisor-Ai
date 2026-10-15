

import asyncio
import os
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from google import genai
from dotenv import load_dotenv

load_dotenv()

WEBAPP_URL = "https://hozirchalik-manzili"

webapp_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="🌐 Advisor AI saytini ochish",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]
    ],
    resize_keyboard=True
)


BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError(
        ".env faylida BOT_TOKEN va GEMINI_API_KEY ni tekshiring."
    )

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
ai_client = genai.Client(api_key=GEMINI_API_KEY)

MODEL = "gemini-3.5-flash-lite"



@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "👋 Salom! Men Advisor AI.\n\n"
        "Biznes g‘oyalar, marketing va daromad "
        "rejalashtirishda yordam beraman.\n\n"
        "💡 Biznes g‘oyasi — yangi g‘oya so‘rang\n"
        "🧮 /foyda — foydani hisoblash\n"
        "❓ /help — yordam",
        reply_markup=webapp_keyboard
    )



@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "🤖 Advisor yordam markazi\n\n"
        "Oddiy xabar yozing — biznes bo‘yicha maslahat oling.\n\n"
        "/start — Boshlash\n"
        "/foyda — Foyda hisoblash\n"
        "/help — Yordam"
    )


@dp.message(Command("foyda"))
async def profit_help(message: Message):
    await message.answer(
        "🧮 Foyda hisoblash\n\n"
        "Masalan:\n"
        "/hisob 10 15000 9000\n\n"
        "Tartibi: miqdor, sotuv narxi, "
        "bitta mahsulot tannarxi."
    )


@dp.message( Command("hisob"))
async def calculate_profit(message: Message):
    parts = (message.text or "").split()

    try:
        if len(parts) != 4:
            raise ValueError

        quantity, price, cost = map(int, parts[1:])

        if quantity <= 0 or price < 0 or cost < 0:
            raise ValueError

        revenue = quantity * price
        expenses = quantity * cost
        profit = revenue - expenses

        await message.answer(
            "📊 Hisob-kitob\n\n"
            f"Mahsulot soni: {quantity}\n"
            f"Tushum: {revenue:,} so‘m\n"
            f"Mahsulot tannarxi jami: {expenses:,} so‘m\n"
            f"Yalpi foyda: {profit:,} so‘m\n\n"
            "Eslatma: ijara, reklama, soliq va boshqa "
            "xarajatlar hisobga olinmagan."
        )

    except ValueError:
        await message.answer(
            "Format: /hisob miqdor sotuv_narxi tannarx\n"
            "Masalan: /hisob 10 15000 9000"
        )


@dp.message(F.text)

@dp.message(F.text)
async def ai_handler(message: Message):
    wait = await message.answer("💡 Advisor o‘ylayapti...")

    for attempt in range(3):
        try:
            response = await asyncio.to_thread(
                ai_client.models.generate_content,
                model=MODEL,
                contents=(
                    "Sen Advisor nomli biznes yordamchisisan. "
                    "O‘zbek tilida sodda, aniq va amaliy maslahat ber. "
                    "Daromadni kafolatlama. Xarajatlar va xavflarni "
                    "ham eslat. Foydalanuvchi savoli: "
                    + message.text
                ),
            )

            answer = response.text or "Hozir javob tayyorlay olmadim."
            await wait.edit_text(answer[:4000])
            return

        except Exception as e:
            print("Gemini xatosi:", type(e).__name__, str(e))

            if attempt < 2:
                await asyncio.sleep(2 ** (attempt + 1))
            else:
                await wait.edit_text(
                    "⚠️ Gemini hozir band. "
                    "Birozdan keyin qayta urinib ko‘ring."
                )

async def main():
    print("Advisor Gemini AI ishga tushmoqda!")
    try:
        await dp.start_polling(bot)
    finally:
        ai_client.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
