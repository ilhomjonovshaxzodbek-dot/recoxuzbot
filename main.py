import asyncio
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
import database as db
from middlewares import ActivityMiddleware
from scheduler import setup_scheduler

from handlers import admin, projects, ai_chat, user


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass  # konsolni chalkashtirmaslik uchun health-check loglarini o'chiramiz


def start_health_server():
    """
    Render.com (va shunga o'xshash) bepul 'Web Service' rejasi faqat
    HTTP portini tinglaydigan servislarni bepul ushlab turadi.
    Shuning uchun bot bilan bir vaqtda shu oddiy HTTP server ham ishga tushadi.
    """
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()


async def main():
    logging.basicConfig(level=logging.INFO)

    db.init_db()
    start_health_server()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(ActivityMiddleware())

    # Tartib muhim: admin va maxsus state'li routerlar birinchi,
    # eng oxirida umumiy "user" routeri (u ichida anonim suhbat relay handleri bor)
    dp.include_router(admin.router)
    dp.include_router(projects.router)
    dp.include_router(ai_chat.router)
    dp.include_router(user.router)

    setup_scheduler(bot)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
