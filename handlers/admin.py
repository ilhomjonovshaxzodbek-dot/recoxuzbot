from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, BaseFilter

from config import ADMIN_IDS
import database as db
import keyboards as kb

router = Router()


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_IDS


# faqat shu routerdagi barcha handlerlar admin uchun ishlashi kerak
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class AdminState(StatesGroup):
    waiting_project_content = State()
    waiting_block_id = State()
    waiting_block_hours = State()
    waiting_broadcast = State()
    waiting_ad_post = State()
    waiting_user_info_id = State()
    waiting_unblock_id = State()
    waiting_ban_id = State()
    waiting_bot_info = State()


@router.message(Command("admin"))
async def open_admin_panel(message: Message):
    await message.answer("Admin panelga xush kelibsiz.", reply_markup=kb.admin_main_menu())


@router.message(F.text == "⬅️ Chiqish")
async def close_admin_panel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Admin paneldan chiqdingiz.", reply_markup=kb.user_main_menu())


@router.message(F.text == "❌ Bekor qilish")
async def admin_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=kb.admin_main_menu())


# ---------- Loyiha qo'shish (admin o'zi, avtomatik tasdiqlangan) ----------

@router.message(F.text == "➕ Loyiha qo'shish")
async def admin_add_project_start(message: Message, state: FSMContext):
    await state.set_state(AdminState.waiting_project_content)
    await message.answer("Loyiha matnini yuboring:", reply_markup=kb.cancel_kb())


@router.message(AdminState.waiting_project_content)
async def admin_add_project_receive(message: Message, state: FSMContext, bot: Bot):
    content = message.text
    db.add_project(message.from_user.id, content, auto_approve=True)
    await state.clear()
    await message.answer("Loyiha qo'shildi va barchaga yuborildi.", reply_markup=kb.admin_main_menu())

    for user in db.get_all_users():
        try:
            await bot.send_message(user["chat_id"], f"🆕 Yangi loyiha:\n\n{content}")
        except Exception:
            pass


# ---------- Bloklash ----------

@router.message(F.text == "🚫 Bloklash")
async def admin_block_start(message: Message, state: FSMContext):
    await state.set_state(AdminState.waiting_block_id)
    await message.answer("Bloklanadigan foydalanuvchi ID sini yuboring:", reply_markup=kb.cancel_kb())


@router.message(AdminState.waiting_block_id)
async def admin_block_get_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("ID raqam bo'lishi kerak, qayta yuboring:")
        return
    await state.update_data(block_id=int(message.text))
    await state.set_state(AdminState.waiting_block_hours)
    await message.answer("Necha soatga bloklansin? (masalan: 3)")


@router.message(AdminState.waiting_block_hours)
async def admin_block_get_hours(message: Message, state: FSMContext, bot: Bot):
    try:
        hours = float(message.text)
    except ValueError:
        await message.answer("Son kiriting, masalan: 3")
        return
    data = await state.get_data()
    chat_id = data["block_id"]
    until = db.block_user(chat_id, hours)
    await state.clear()
    await message.answer(f"Foydalanuvchi {chat_id} {hours} soatga bloklandi.", reply_markup=kb.admin_main_menu())
    try:
        import time
        until_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(until))
        await bot.send_message(chat_id, f"🚫 Siz bloklandingiz. Blok {until_str} da tugaydi.")
    except Exception:
        pass


# ---------- Blokdan ochish ----------

@router.message(F.text == "✅ Blokdan ochish")
async def admin_unblock_start(message: Message, state: FSMContext):
    await state.set_state(AdminState.waiting_unblock_id)
    await message.answer("Blokdan chiqariladigan foydalanuvchi ID sini yuboring:", reply_markup=kb.cancel_kb())


@router.message(AdminState.waiting_unblock_id)
async def admin_unblock_receive(message: Message, state: FSMContext, bot: Bot):
    if not message.text.isdigit():
        await message.answer("ID raqam bo'lishi kerak, qayta yuboring:")
        return
    chat_id = int(message.text)
    db.unblock_user(chat_id)
    await state.clear()
    await message.answer(f"Foydalanuvchi {chat_id} blokdan chiqarildi.", reply_markup=kb.admin_main_menu())
    try:
        await bot.send_message(chat_id, "✅ Siz blokdan chiqarildingiz.")
    except Exception:
        pass


# ---------- Foydalanuvchilarni kuzatish ----------

@router.message(F.text == "👀 Foydalanuvchilarni kuzatish")
async def admin_track_users(message: Message):
    users = db.get_all_users()
    if not users:
        await message.answer("Hozircha foydalanuvchi yo'q.")
        return
    text = f"Jami foydalanuvchilar: {len(users)}\n\n"
    for u in users[:30]:
        name = u["first_name"] or u["username"] or str(u["chat_id"])
        status = "🚫 bloklangan" if db.is_blocked(u["chat_id"]) else "✅ faol"
        text += f"{u['chat_id']} — {name} — {status}\n"
    await message.answer(text)


# ---------- Foydalanuvchi ma'lumotini ko'rish ----------

@router.message(F.text == "ℹ️ Foydalanuvchi ma'lumotini ko'rish")
async def admin_user_info_start(message: Message, state: FSMContext):
    await state.set_state(AdminState.waiting_user_info_id)
    await message.answer("Foydalanuvchi ID sini yuboring:", reply_markup=kb.cancel_kb())


@router.message(AdminState.waiting_user_info_id)
async def admin_user_info_receive(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("ID raqam bo'lishi kerak, qayta yuboring:")
        return
    user = db.get_user(int(message.text))
    await state.clear()
    if not user:
        await message.answer("Foydalanuvchi topilmadi.", reply_markup=kb.admin_main_menu())
        return
    text = (
        f"ID: {user['chat_id']}\n"
        f"Ism: {user['first_name']}\n"
        f"Username: @{user['username']}\n"
        f"Bugungi faollik: {(user['daily_active_seconds'] or 0)//60} daqiqa\n"
        f"Bloklanganmi: {'Ha' if db.is_blocked(user['chat_id']) else 'Yoq'}\n"
        f"Butunlay chiqarilganmi: {'Ha' if user['is_banned'] else 'Yoq'}\n"
    )
    await message.answer(text, reply_markup=kb.admin_main_menu())


# ---------- Hammaga xabar yuborish ----------

@router.message(F.text == "📨 Hammaga xabar yuborish")
async def admin_broadcast_start(message: Message, state: FSMContext):
    await state.set_state(AdminState.waiting_broadcast)
    await message.answer("Barchaga yuboriladigan xabarni kiriting:", reply_markup=kb.cancel_kb())


@router.message(AdminState.waiting_broadcast)
async def admin_broadcast_send(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    count = 0
    for user in db.get_all_users():
        try:
            await bot.send_message(user["chat_id"], message.text)
            count += 1
        except Exception:
            pass
    await message.answer(f"Xabar {count} ta foydalanuvchiga yuborildi.", reply_markup=kb.admin_main_menu())


# ---------- E'lon berish (reklama bilan) ----------

@router.message(F.text == "📣 E'lon berish")
async def admin_ad_post_start(message: Message, state: FSMContext):
    await state.set_state(AdminState.waiting_ad_post)
    await message.answer("E'lon/reklama matnini (yoki rasm+matn) yuboring:", reply_markup=kb.cancel_kb())


@router.message(AdminState.waiting_ad_post)
async def admin_ad_post_send(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    count = 0
    for user in db.get_all_users():
        try:
            if message.photo:
                await bot.send_photo(user["chat_id"], message.photo[-1].file_id, caption=message.caption)
            else:
                await bot.send_message(user["chat_id"], message.text)
            count += 1
        except Exception:
            pass
    await message.answer(f"E'lon {count} ta foydalanuvchiga yuborildi.", reply_markup=kb.admin_main_menu())


# ---------- Botni to'xtatish / yoqish ----------

@router.message(F.text == "⏸ Botni to'xtatish")
async def admin_pause_bot(message: Message):
    db.set_bot_paused(True)
    await message.answer("Bot vaqtincha to'xtatildi. Foydalanuvchilar javob ololmaydi.", reply_markup=kb.admin_main_menu())


@router.message(F.text == "▶️ Botni yoqish")
async def admin_resume_bot(message: Message):
    db.set_bot_paused(False)
    await message.answer("Bot qayta ishga tushirildi.", reply_markup=kb.admin_main_menu())


# ---------- Foydalanuvchini butunlay chiqarib yuborish ----------

@router.message(F.text == "⛔️ Foydalanuvchini chiqarib yuborish")
async def admin_ban_start(message: Message, state: FSMContext):
    await state.set_state(AdminState.waiting_ban_id)
    await message.answer("Butunlay chiqariladigan foydalanuvchi ID sini yuboring:", reply_markup=kb.cancel_kb())


@router.message(AdminState.waiting_ban_id)
async def admin_ban_receive(message: Message, state: FSMContext, bot: Bot):
    if not message.text.isdigit():
        await message.answer("ID raqam bo'lishi kerak, qayta yuboring:")
        return
    chat_id = int(message.text)
    db.ban_user(chat_id)
    await state.clear()
    await message.answer(f"Foydalanuvchi {chat_id} botdan butunlay chiqarib yuborildi.", reply_markup=kb.admin_main_menu())
    try:
        await bot.send_message(chat_id, "Siz botdan butunlay chiqarib yuborildingiz.")
    except Exception:
        pass


# ---------- Bot ma'lumotini o'zgartirish ----------

@router.message(F.text == "✏️ Bot ma'lumotini o'zgartirish")
async def admin_bot_info_start(message: Message, state: FSMContext):
    await state.set_state(AdminState.waiting_bot_info)
    current = db.get_bot_info()
    await message.answer(
        f"Joriy bot ma'lumoti:\n{current or '(bo\u2018sh)'}\n\nYangi matnni yuboring:",
        reply_markup=kb.cancel_kb(),
    )


@router.message(AdminState.waiting_bot_info)
async def admin_bot_info_receive(message: Message, state: FSMContext):
    db.set_bot_info(message.text)
    await state.clear()
    await message.answer("Bot ma'lumoti yangilandi.", reply_markup=kb.admin_main_menu())
