import os
from dotenv import load_dotenv

load_dotenv()  # lokalda .env faylini o'qiydi; Railway'da bu chaqiruv hech narsaga ta'sir qilmaydi

# Railway'da yoki lokal .env faylida o'rnatiladigan environment variable'lar
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Admin(lar) chat_id si (vergul bilan ajratib bir nechta admin qo'yish mumkin)
# Masalan Railway Variables ichida: ADMIN_IDS=123456789,987654321
ADMIN_IDS = [
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
]

# Faollik talablari (soniyada)
DAILY_ACTIVE_SECONDS_REQUIRED = 30 * 60  # 30 daqiqa (kerak bo'lsa 3600 ga o'zgartiring)
MAX_BLOCK_HOURS = 3

# Groq model nomi
GROQ_MODEL = "llama-3.3-70b-versatile"

DB_PATH = "bot.db"
