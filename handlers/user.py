from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, BaseFilter

from config import ADMIN_IDS
import database as db
import keyboards as kb

router = Router()


class InActiveChat(BaseFilter):
    """Foydalanuvchi hozir anonim suhbatda (boshqa userga ulangan) bo'lsa True qaytaradi."""

    async def __call__(self, message: Message) -> bool:
        return db.get_chat_partner(message.from_user.id) is not None


class MsgState(StatesGroup):
    waiting_ad = State()
    waiting_announcement = State()
    waiting_admin_message = State()
    waiting_negative = State()


@router.message(CommandStart())
async def cmd_start(message: Message):
    db.add_user_if_not_exists(
        message.from_user.id, message.from_user.first_name, message.from_user.username
    )
    if db.is_banned(message.from_user.id):
        await message.answer("Siz botdan butunlay chiqarib yuborilgansiz.")
        return
    await message.answer(
        "🤖 <b>RecoX</b>ga xush kelibsiz! Quyidagi menyudan birini tanlang:",
        reply_markup=kb.user_main_menu(),
    )


# ---------- Oddiy matn kiritish talab qiladigan tugmalar ----------

@router.message(F.text == "📢 Reklama")
async def ask_ad(message: Message, state: FSMContext):
    await state.set_state(MsgState.waiting_ad)
    await message.answer("Reklama matningizni yuboring:", reply_markup=kb.cancel_kb())


@router.message(F.text == "📣 E'lon")
async def ask_announcement(message: Message, state: FSMContext):
    await state.set_state(MsgState.waiting_announcement)
    await message.answer("E'lon matningizni yuboring:", reply_markup=kb.cancel_kb())


@router.message(F.text == "✉️ Adminga xabar yozish")
async def ask_admin_message(message: Message, state: FSMContext):
    await state.set_state(MsgState.waiting_admin_message)
    await message.answer("Adminga xabaringizni yozing:", reply_markup=kb.cancel_kb())


@router.message(F.text == "⚠️ Negativ yozish")
async def ask_negative(message: Message, state: FSMContext):
    await state.set_state(MsgState.waiting_negative)
    await message.answer("Fikr-mulohaza/shikoyatingizni yozing:", reply_markup=kb.cancel_kb())


@router.message(F.text == "❌ Bekor qilish")
async def cancel_any(message: Message, state: FSMContext):
    current = await state.get_state()
    if current in (
        MsgState.waiting_ad, MsgState.waiting_announcement,
        MsgState.waiting_admin_message, MsgState.waiting_negative,
    ):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=kb.user_main_menu())


async def _forward_to_admins(bot: Bot, prefix: str, message: Message):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"{prefix}\nYuboruvchi: {message.from_user.full_name} (id: {message.from_user.id})\n\n{message.text}",
            )
        except Exception:
            pass


@router.message(MsgState.waiting_ad)
async def receive_ad(message: Message, state: FSMContext, bot: Bot):
    await _forward_to_admins(bot, "📢 Yangi reklama so'rovi", message)
    await state.clear()
    await message.answer("Reklamangiz adminga yuborildi.", reply_markup=kb.user_main_menu())


@router.message(MsgState.waiting_announcement)
async def receive_announcement(message: Message, state: FSMContext, bot: Bot):
    await _forward_to_admins(bot, "📣 Yangi e'lon so'rovi", message)
    await state.clear()
    await message.answer("E'loningiz adminga yuborildi.", reply_markup=kb.user_main_menu())


@router.message(MsgState.waiting_admin_message)
async def receive_admin_message(message: Message, state: FSMContext, bot: Bot):
    await _forward_to_admins(bot, "✉️ Foydalanuvchidan xabar", message)
    await state.clear()
    await message.answer("Xabaringiz adminga yetkazildi.", reply_markup=kb.user_main_menu())


@router.message(MsgState.waiting_negative)
async def receive_negative(message: Message, state: FSMContext, bot: Bot):
    await _forward_to_admins(bot, "⚠️ Negativ fikr", message)
    await state.clear()
    await message.answer("Fikringiz uchun rahmat, adminga yetkazildi.", reply_markup=kb.user_main_menu())


# ---------- Hafta aktivlari ----------

@router.message(F.text == "📊 Hafta aktivlarini ko'rish")
async def weekly_active(message: Message):
    users = db.get_all_users()
    sorted_users = sorted(users, key=lambda u: u["daily_active_seconds"] or 0, reverse=True)
    top = sorted_users[:10]
    if not top:
        await message.answer("Hozircha ma'lumot yo'q.")
        return
    text = "📊 Eng faol foydalanuvchilar (bugungi kun):\n\n"
    for i, u in enumerate(top, start=1):
        name = u["first_name"] or u["username"] or str(u["chat_id"])
        minutes = (u["daily_active_seconds"] or 0) // 60
        text += f"{i}. {name} — {minutes} daqiqa\n"
    await message.answer(text)


# ---------- Boshqa foydalanuvchilar bilan suhbat ----------

@router.message(F.text == "👥 Boshqa foydalanuvchilar bilan suhbat")
async def show_users_for_chat(message: Message):
    users = [u for u in db.get_all_users() if u["chat_id"] != message.from_user.id]
    if not users:
        await message.answer("Hozircha boshqa foydalanuvchilar yo'q.")
        return
    await message.answer("Suhbatlashish uchun foydalanuvchini tanlang:", reply_markup=kb.users_list_kb(users))


@router.callback_query(F.data.startswith("chat_req:"))
async def send_chat_request(callback: CallbackQuery, bot: Bot):
    to_id = int(callback.data.split(":")[1])
    from_id = callback.from_user.id

    if to_id == from_id:
        await callback.answer("O'zingizga so'rov yubora olmaysiz.", show_alert=True)
        return

    req_id = db.create_chat_request(from_id, to_id)
    await callback.answer("So'rov yuborildi.")

    try:
        await bot.send_message(
            to_id,
            "👥 Sizga anonim suhbat so'rovi keldi.",
            reply_markup=kb.chat_request_kb(req_id),
        )
    except Exception:
        await callback.message.answer("Bu foydalanuvchiga so'rov yubora olmadik.")


@router.callback_query(F.data.startswith("chat_accept:"))
async def accept_chat(callback: CallbackQuery, bot: Bot):
    req_id = int(callback.data.split(":")[1])
    req = db.get_chat_request(req_id)
    if not req or req["status"] != "pending":
        await callback.answer("So'rov endi amal qilmaydi.", show_alert=True)
        return

    db.set_chat_request_status(req_id, "accepted")
    db.start_active_chat(req["from_id"], req["to_id"])

    await callback.message.edit_text("✅ Suhbatga rozilik berdingiz.")
    await callback.answer()

    for uid in (req["from_id"], req["to_id"]):
        try:
            await bot.send_message(
                uid,
                "Anonim suhbat boshlandi! Xabar yozishingiz mumkin.\nTugatish uchun \"🔚 Suhbatni tugatish\" tugmasini bosing.",
                reply_markup=kb.end_chat_kb(),
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("chat_decline:"))
async def decline_chat(callback: CallbackQuery):
    req_id = int(callback.data.split(":")[1])
    db.set_chat_request_status(req_id, "declined")
    await callback.message.edit_text("❌ Suhbat rad etildi.")
    await callback.answer()


@router.message(F.text == "🔚 Suhbatni tugatish")
async def end_chat(message: Message, bot: Bot):
    partner_id = db.end_active_chat(message.from_user.id)
    await message.answer("Suhbat tugatildi.", reply_markup=kb.user_main_menu())
    if partner_id:
        try:
            await bot.send_message(partner_id, "Suhbatdoshingiz suhbatni tugatdi.", reply_markup=kb.user_main_menu())
        except Exception:
            pass


@router.message(InActiveChat(), F.text)
async def relay_active_chat(message: Message, bot: Bot):
    """
    Agar foydalanuvchi faol anonim suhbatda bo'lsa, xabarini suhbatdoshiga yetkazadi.
    Yuqoridagi aniq tugma handlerlari birinchi tekshirilgani uchun ular ustuvor bo'ladi;
    shu handler faqat foydalanuvchi haqiqatan faol suhbatda bo'lgandagina ishlaydi.
    """
    partner_id = db.get_chat_partner(message.from_user.id)
    if partner_id:
        try:
            await bot.send_message(partner_id, message.text)
        except Exception:
            pass
