import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message

import database as db
from config import ADMIN_IDS


class ActivityMiddleware(BaseMiddleware):
    """
    Har xabar kelganda:
    - foydalanuvchini bazaga qo'shadi (agar yo'q bo'lsa)
    - butunlay chiqarilgan (banned) bo'lsa - to'xtatadi
    - bloklangan bo'lsa - xabar berib to'xtatadi
    - bot pauzada bo'lsa (admin bundan mustasno) - to'xtatadi
    - aks holda kunlik faollik hisoblagichini yangilaydi
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id

        db.add_user_if_not_exists(user_id, event.from_user.first_name, event.from_user.username)

        if db.is_banned(user_id):
            await event.answer("Siz botdan butunlay chiqarib yuborilgansiz.")
            return

        if db.is_blocked(user_id):
            user = db.get_user(user_id)
            until_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(user["blocked_until"]))
            await event.answer(f"🚫 Siz hozircha bloklangansiz. Blok {until_str} da tugaydi.")
            return

        if db.is_bot_paused() and user_id not in ADMIN_IDS:
            await event.answer("Bot hozircha texnik ishlar uchun to'xtatilgan. Birozdan so'ng qayta urinib ko'ring.")
            return

        db.touch_activity(user_id, seconds_delta=60)

        return await handler(event, data)
