# 🤖 Sun'iy Intellektli Telegram Bot (ChatGPT varianti)

Ushbu bot **Google Gemini AI**, **DuckDuckGo Real-Time Search**, **Ob-havo servisi** va **aiogram 3** asosida yaratilgan universal sun'iy intellekt botidir.

---

## ✨ Imkoniyatlar
- 🧠 **Universal AI (ChatGPT kabi)**: Dasturlash, fan, tillar, biznes, tarix va kundalik har qanday savollarga to'liq javob bera oladi.
- 🌦 **Jonli va aniq ob-havo**: Masalan, *«Bugun Qashqadaryo Kitob ob-havosi qanday?»* deb so'ralsa, real vaqtdagi ob-havo (harorat, shamol, namlik, tavsiyalar)ni aniq yetkazadi.
- 🌍 **Dunyo yangiliklari**: Internet orqali eng so'nggi yangiliklar, valyuta kurslari va dolzarb xabarlarni topib beradi.
- 💬 **Suhbat xotirasi (Context)**: Har bir foydalanuvchining oldingi xabarlarini eslab qoladi.
- ⚡ **Render.com mosligi**: Render Web Service va Background Worker muhitlarida uzluksiz ishlash uchun sozlangan.

---

## 📁 Loyiha tarkibi
- [`bot.py`](bot.py) — Telegram bot va Render salomatlik serveri (`aiohttp`).
- [`ai_service.py`](ai_service.py) — Google Gemini AI integratsiyasi va xotira boshqaruvi.
- [`tools.py`](tools.py) — Jonli ob-havo va internetdan qidirish vositalari.
- [`render.yaml`](render.yaml) — Render blueprint konfiguratsiyasi.
- [`Procfile`](Procfile) — Render web jarayoni uchun buyruq.
- [`requirements.txt`](requirements.txt) — Kutubxonalar ro'yxati.
- [`.env.example`](.env.example) — Muhit o'zgaruvchilari namunasi.

---

## 🚀 Mahaliy muhitda ishga tushirish

1. Kutubxonalarni o'rnatish:
   ```bash
   pip install -r requirements.txt
   ```
2. `.env` faylida tokenlarni to'ldirish:
   ```env
   BOT_TOKEN=your_bot_token_here
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-3.5-flash
   PORT=10000
   ```
3. Botni ishga tushirish:
   ```bash
   python bot.py
   ```

---

## 🌐 Render.com ga joylash (Deploy qilish)

1. [Render.com](https://render.com) ga kiring va GitHub hisobingiz bilan bog'lang.
2. **New +** tugmasini bosib, **Web Service** ni tanlang.
3. GitHub repozitoriyangizni (`mashhulot`) tanlang.
4. Quyidagi parametrlarni kiriting:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
5. **Environment Variables** (Muhit o'zgaruvchilari) bo'limiga qo'shing:
   - `BOT_TOKEN` = Sizning Telegram Bot tokeningiz
   - `GEMINI_API_KEY` = Sizning Gemini API kalitingiz
   - `GEMINI_MODEL` = `gemini-3.5-flash`
   - `PORT` = `10000`
6. **Deploy Web Service** tugmasini bosing. Bot Renderda 24/7 ishlab turadi!
