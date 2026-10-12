import os
import asyncio
import logging
from typing import Dict, List
from google import genai
from google.genai import types, errors

from tools import get_weather, search_web

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Siz — Telegramda faoliyat yurituvchi, juda aqlli, muloyim va har tomonlama bilimdon sun'iy intellekt yordamchisisiz (ChatGPT ning mukammal Telegram versiyasi).\n\n"
    "Qoidalaringiz:\n"
    "1. Dunyo yangiliklari, ob-havo, fan, dasturlash, tarix, biznes, psixologiya, tillar va kundalik masalalarni chuqur bilasiz.\n"
    "2. Har qanday savolga aniq, to'liq, mantiqiy va o'zbek tilida (yoki foydalanuvchi so'ragan tilda) chiroyli javob bering.\n"
    "3. Agar xabarda jonli faktlar (ob-havo ma'lumotlari yoki internet qidiruvi natijalari) taqdim etilsa, aynan shu ma'lumotlarga tayanib 100% aniq va to'liq javob bering (masalan: harorat, holat, shamol, tavsiyalar).\n"
    "4. Javoblaringizni Telegram uchun chiroyli qilib formatlang (abzaslar, ro'yxatlar, mos emojilar)."
)

class GeminiService:
    def __init__(self, api_key: str, default_model: str = "gemini-3.5-flash"):
        self.api_key = api_key
        # Tezkor ulanish va ortiqcha kutishlarning oldini olish uchun timeout va retry sozlamalari
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(attempts=1),
                timeout=20000
            )
        )
        self.candidate_models = [
            default_model,
            "gemini-3.5-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash-lite",
            "gemini-flash-latest",
        ]
        # Foydalanuvchilar tarixi (xotira): user_id -> list of message dicts
        self.user_histories: Dict[int, List[dict]] = {}

    def reset_chat(self, user_id: int):
        """Foydalanuvchi bilan bo'lgan suhbat xotirasini tozalash"""
        if user_id in self.user_histories:
            del self.user_histories[user_id]

    def _extract_location(self, text: str) -> str:
        """Matndan shahar/tuman nomini aniqlash"""
        lower = text.lower()
        uzb_places = [
            "kitob", "qashqadaryo", "qarshi", "shaxrisabz", "shahrisabz", "g'uzor", "koson",
            "muborak", "chiroqchi", "yakkabog'", "dehqonobod", "nishon", "kasbi",
            "toshkent", "tashkent", "samarqand", "samarkand", "buxoro", "andijon", "farg'ona",
            "namangan", "nukus", "navoiy", "jizzax", "guliston", "termiz", "urganch", "xiva"
        ]
        for place in uzb_places:
            if place in lower:
                return place.capitalize()
        return "Kitob" if "kitob" in lower else "Toshkent"

    def _is_weather_query(self, text: str) -> bool:
        keywords = ["ob-havo", "obhavo", "ob havo", "harorat", "yomg'ir", "qor yog", "quyoshli", "havo qanday", "havo ma'lumot"]
        return any(k in text.lower() for k in keywords)

    def _is_news_or_realtime(self, text: str) -> bool:
        keywords = [
            "yangilik", "dunyo yangilik", "xabar", "nima gap", "nima yangilik",
            "dollar", "kurs", "valyuta", "bugun nima bo'ldi", "so'nggi voqea", "hozirgi"
        ]
        return any(k in text.lower() for k in keywords)

    async def generate_reply(self, user_id: int, user_message: str) -> str:
        return await asyncio.to_thread(self._sync_generate_reply, user_id, user_message)

    def _sync_generate_reply(self, user_id: int, user_message: str) -> str:
        live_facts = ""

        # 1. Ob-havo so'rovi bo'lsa jonli ma'lumot olish
        if self._is_weather_query(user_message):
            loc = self._extract_location(user_message)
            logger.info(f"Ob-havo qidirilmoqda: {loc}")
            weather_data = get_weather(loc)
            live_facts += f"\n[Jonli ob-havo ma'lumotlari ({loc})]:\n{weather_data}\n"

        # 2. Yangiliklar yoki eng so'nggi real-vaqt so'rovi bo'lsa internetdan qidirish
        elif self._is_news_or_realtime(user_message):
            logger.info(f"Internetdan qidirilmoqda: {user_message}")
            search_data = search_web(user_message, max_results=3)
            live_facts += f"\n[Internetdan so'nggi ma'lumotlar]:\n{search_data}\n"

        if user_id not in self.user_histories:
            self.user_histories[user_id] = []

        augmented_user_message = user_message
        if live_facts:
            augmented_user_message = f"{user_message}\n\n[ANiQ REAL-VAQT FAKTLARI (FOYDALANING)]:\n{live_facts}"

        self.user_histories[user_id].append({"role": "user", "text": augmented_user_message})

        # Kontekst hajmini so'nggi 10 ta xabar bilan cheklash
        if len(self.user_histories[user_id]) > 10:
            self.user_histories[user_id] = self.user_histories[user_id][-10:]

        # Promptni yig'ish
        prompt_builder = [f"Tizim: {SYSTEM_PROMPT}\n"]
        for msg in self.user_histories[user_id]:
            role_name = "Foydalanuvchi" if msg["role"] == "user" else "Assistant"
            prompt_builder.append(f"{role_name}: {msg['text']}")
        prompt_builder.append("Assistant: ")
        full_prompt = "\n\n".join(prompt_builder)

        # Modellarni ketma-ket sinab ko'rish
        for model_name in self.candidate_models:
            try:
                res = self.client.models.generate_content(
                    model=model_name,
                    contents=full_prompt
                )
                if res and res.text:
                    reply_text = res.text.strip()
                    self.user_histories[user_id].append({"role": "assistant", "text": reply_text})
                    return reply_text
            except Exception as e:
                logger.warning(f"Model '{model_name}' xatosi: {e}. Keyingi modelga o'tilmoqda...")
                continue

        # Agar barcha modellar band bo'lsa va jonli faktlar bo'lsa
        if live_facts:
            return f"Hurmatli foydalanuvchi, so'rovingiz bo'yicha jonli ma'lumot:\n\n{live_facts}"

        return "Kechirasiz, sun'iy intellekt serverida qisqa muddatli yuklama bo'ldi. Iltimos, yana bir bor so'rab ko'ring."
