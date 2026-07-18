import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

import database as db
from config import DAILY_ACTIVE_SECONDS_REQUIRED, MAX_BLOCK_HOURS


async def check_daily_activity(bot: Bot):
    """
    Har kuni belgilangan soatda (masalan 23:00) ishga tushadi:
    kunlik talab qilingan faollikka yetmagan foydalanuvchilarni bloklaydi.
    """
    today = time.strftime("%Y-%m-%d")
    for user in db.get_all_users():
        if user["day_marker"] != today:
            # bugun umuman faol bo'lmagan
            active_seconds = 0
        else:
            active_seconds = user["daily_active_seconds"] or 0

        if active_seconds < DAILY_ACTIVE_SECONDS_REQUIRED and not db.is_blocked(user["chat_id"]):
            until = db.block_user(user["chat_id"], MAX_BLOCK_HOURS)
            until_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(until))
            try:
                await bot.send_message(
                    user["chat_id"],
                    f"🚫 Bugun botda yetarlicha faol bo'lmadingiz. Siz bloklandingiz.\n"
                    f"Blok {until_str} da tugaydi.",
                )
            except Exception:
                pass


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    # Har kuni soat 23:00 da faollikni tekshiradi (kerak bo'lsa vaqtni o'zgartiring)
    scheduler.add_job(check_daily_activity, "cron", hour=23, minute=0, args=[bot])
    scheduler.start()
    return scheduler
