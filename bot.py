import os
import sys
import logging
import asyncio
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.enums import ChatAction
from aiogram.utils.chat_action import ChatActionSender
from aiohttp import web

from ai_service import GeminiService
from tools import get_weather, search_web

# Muhit o'zgaruvchilarini yuklash
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
PORT = int(os.getenv("PORT", 10000))

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Servis va Bot
ai_service = GeminiService(api_key=GEMINI_API_KEY, default_model=GEMINI_MODEL)
dp = Dispatcher()

def split_text(text: str, max_length: int = 4000) -> list[str]:
    """Telegramning 4096 belgili limitidan oshib ketmaslik uchun bo'laklash"""
    parts = []
    while len(text) > max_length:
        split_at = text.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length
        parts.append(text[:split_at])
        text = text[split_at:].lstrip()
    if text:
        parts.append(text)
    return parts

# Web server (Render salomatlik tekshiruvi - Health Check uchun)
async def handle_ping(request):
    return web.Response(text="OK - Bot is running successfully!", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Render uchun Web Server ishga tushdi (Port: {PORT})")

@dp.message(CommandStart())
async def handle_start(message: Message):
    user_name = message.from_user.first_name if message.from_user else "Do'stim"
    welcome_text = (
        f"Assalomu alaykum, {user_name}! 👋\n\n"
        "Men — har qanday savolingizga javob beradigan, dunyo yangiliklari va aniq ob-havoni biladigan aqlli sun'iy intellekt botiman (ChatGPT Telegram versiyasi)!\n\n"
        "Menga istalgan savolingizni yuborishingiz mumkin:\n"
        "🌦 «Bugun Qashqadaryo Kitob ob-havosi qanday?»\n"
        "🌍 «Dunyoda qanday yangiliklar bor?»\n"
        "💡 Dasturlash, fan, tillar, biznes yoki istalgan mavzudagi savollar.\n\n"
        "Foydali buyruqlar:\n"
        "/clear - Suhbat xotirasini tozalash (yangi mavzu boshlash)\n"
        "/news - So'nggi dunyo yangiliklari\n"
        "/weather <shahar> - Ob-havo ma'lumoti\n"
        "/help - Yordam"
    )
    await message.answer(welcome_text)

@dp.message(Command("clear"))
async def handle_clear(message: Message):
    ai_service.reset_chat(message.from_user.id)
    await message.answer("Suhbat xotirasi tozalandi! Endi yangi mavzuda suhbatlashishimiz mumkin. ✨")

@dp.message(Command("help"))
async def handle_help(message: Message):
    help_text = (
        "🤖 Bot imkoniyatlari:\n\n"
        "1. **Universal Sun'iy Intellekt**: Savollarga to'liq va atroflicha javob beradi.\n"
        "2. **Jonli Ob-havo**: Kitob, Toshkent yoki istalgan shahar ob-havosini so'rang.\n"
        "3. **Dunyo Yangiliklari**: Internetdan eng yangi voqea va xabarlarni topib beradi.\n"
        "4. **Suhbat Xotirasi**: Oldingi yozganlaringizni eslab turadi.\n\n"
        "Buyruqlar:\n"
        "/clear - Xotirani tozalash\n"
        "/news - Eng so'nggi yangiliklar\n"
        "/weather Toshkent - Ob-havo tekshirish"
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("news"))
async def handle_news_command(message: Message, bot: Bot):
    async with ChatActionSender(bot=bot, chat_id=message.chat.id, action=ChatAction.TYPING):
        news_prompt = "Bugungi eng muhim dunyo va O'zbekiston yangiliklarini qisqa va qiziqarli qilib saralab ber."
        reply = await ai_service.generate_reply(user_id=message.from_user.id, user_message=news_prompt)
    for chunk in split_text(reply):
        await message.answer(chunk)

@dp.message(Command("weather"))
async def handle_weather_command(message: Message, bot: Bot):
    args = message.text.split(maxsplit=1)
    location = args[1] if len(args) > 1 else "Kitob"
    async with ChatActionSender(bot=bot, chat_id=message.chat.id, action=ChatAction.TYPING):
        weather_prompt = f"Bugun {location} shahrida ob-havo qanday bo'ladi?"
        reply = await ai_service.generate_reply(user_id=message.from_user.id, user_message=weather_prompt)
    for chunk in split_text(reply):
        await message.answer(chunk)

@dp.message(F.text)
async def handle_chat_message(message: Message, bot: Bot):
    user_id = message.from_user.id
    user_text = message.text

    # Telegramda 'yozmoqda...' animatsiyasi
    async with ChatActionSender(bot=bot, chat_id=message.chat.id, action=ChatAction.TYPING):
        reply_text = await ai_service.generate_reply(user_id=user_id, user_message=user_text)

    # Javobni yuborish
    for chunk in split_text(reply_text):
        await message.answer(chunk)

async def main():
    if not BOT_TOKEN or "YOUR" in BOT_TOKEN:
        logger.error("BOT_TOKEN ko'rsatilmagan! .env faylini tekshiring.")
        return

    # 1. Render talab qiladigan Web Serverni fonda ishga tushirish
    try:
        await start_web_server()
    except Exception as e:
        logger.warning(f"Web serverni ishga tushirishda ogohlantirish: {e}")

    # 2. Telegram Bot polling boshlash
    bot = Bot(token=BOT_TOKEN)
    logger.info("Bot muvaffaqiyatli ishga tushdi va xabarlarni qabul qilmoqda!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
