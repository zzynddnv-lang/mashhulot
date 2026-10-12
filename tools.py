import requests
from typing import Optional
from ddgs import DDGS

def get_weather(location: str = "Toshkent") -> str:
    """wttr.in orqali aniq va yangi ob-havo ma'lumotini olish"""
    try:
        # Joy nomini tozalash (masalan 'Kitob' yoki 'Qashqadaryo')
        clean_loc = location.strip().replace(" ", "+")
        url = f"https://wttr.in/{clean_loc}?format=j1"
        response = requests.get(url, timeout=7)
        if response.status_code == 200:
            data = response.json()
            curr = data["current_condition"][0]
            temp = curr["temp_C"]
            feel = curr["FeelsLikeC"]
            desc = curr["weatherDesc"][0]["value"]
            humidity = curr["humidity"]
            wind = curr["windspeedKmph"]

            # Bugungi prognoz (agar mavjud bo'lsa)
            forecast = ""
            if "weather" in data and len(data["weather"]) > 0:
                today = data["weather"][0]
                max_t = today.get("maxtempC", "")
                min_t = today.get("mintempC", "")
                forecast = f" Kunduzgi yuqori harorat: {max_t}°C, kechasi: {min_t}°C."

            return (
                f"Joylashuv: {location}\n"
                f"Hozirgi harorat: {temp}°C (sezilishi: {feel}°C)\n"
                f"Holat: {desc}\n"
                f"Namlik: {humidity}%\n"
                f"Shamol: {wind} km/soat.\n"
                f"{forecast}"
            )
        return f"{location} bo'yicha ob-havo ma'lumotini yuklab bo'lmadi."
    except Exception as e:
        return f"Ob-havo servisi bilan bog'lanishda xatolik: {e}"

def search_web(query: str, max_results: int = 4) -> str:
    """DuckDuckGo orqali internetdan eng so'nggi ma'lumotlar va yangiliklarni qidirish"""
    try:
        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "Qidiruv bo'yicha ma'lumot topilmadi."

        formatted = []
        for i, item in enumerate(results, 1):
            title = item.get("title", "")
            snippet = item.get("body", "")
            link = item.get("href", "")
            formatted.append(f"{i}. {title}\n   {snippet}\n   Manba: {link}")

        return "\n\n".join(formatted)
    except Exception as e:
        return f"Internetdan qidirishda xatolik: {e}"
