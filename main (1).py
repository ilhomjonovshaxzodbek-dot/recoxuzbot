import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
import database as db
from middlewares import ActivityMiddleware
from scheduler import setup_scheduler

from handlers import admin, projects, ai_chat, user


async def main():
    logging.basicConfig(level=logging.INFO)

    db.init_db()

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
