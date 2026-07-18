from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)


# ---------- FOYDALANUVCHI MENYUSI ----------

def user_main_menu() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="🤖 AI bilan suhbat"), KeyboardButton(text="📢 Reklama")],
        [KeyboardButton(text="📣 E'lon"), KeyboardButton(text="✉️ Adminga xabar yozish")],
        [KeyboardButton(text="⚠️ Negativ yozish"), KeyboardButton(text="📊 Hafta aktivlarini ko'rish")],
        [KeyboardButton(text="👥 Boshqa foydalanuvchilar bilan suhbat")],
        [KeyboardButton(text="➕ O'z loyihasini kiritish"), KeyboardButton(text="📁 Loyihalar")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True,
    )


# ---------- ADMIN MENYUSI ----------

def admin_main_menu() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="➕ Loyiha qo'shish"), KeyboardButton(text="🚫 Bloklash")],
        [KeyboardButton(text="👀 Foydalanuvchilarni kuzatish"), KeyboardButton(text="📨 Hammaga xabar yuborish")],
        [KeyboardButton(text="📣 E'lon berish"), KeyboardButton(text="ℹ️ Foydalanuvchi ma'lumotini ko'rish")],
        [KeyboardButton(text="✅ Blokdan ochish"), KeyboardButton(text="⏸ Botni to'xtatish")],
        [KeyboardButton(text="▶️ Botni yoqish"), KeyboardButton(text="⛔️ Foydalanuvchini chiqarib yuborish")],
        [KeyboardButton(text="✏️ Bot ma'lumotini o'zgartirish")],
        [KeyboardButton(text="⬅️ Chiqish")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# ---------- LOYIHA TASDIQLASH (admin uchun inline) ----------

def project_review_kb(project_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Ruxsat etish", callback_data=f"proj_approve:{project_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"proj_reject:{project_id}"),
    ]])


# ---------- FOYDALANUVCHILAR RO'YXATI (suhbat uchun) ----------

def users_list_kb(users) -> InlineKeyboardMarkup:
    rows = []
    for u in users:
        name = u["first_name"] or (u["username"] or str(u["chat_id"]))
        rows.append([InlineKeyboardButton(text=name, callback_data=f"chat_req:{u['chat_id']}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def chat_request_kb(req_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"chat_accept:{req_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"chat_decline:{req_id}"),
    ]])


def end_chat_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔚 Suhbatni tugatish")]],
        resize_keyboard=True,
    )
