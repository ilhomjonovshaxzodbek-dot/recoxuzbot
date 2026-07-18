import time
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
import database as db
import keyboards as kb

router = Router()


class ProjectState(StatesGroup):
    waiting_content = State()


@router.message(F.text == "➕ O'z loyihasini kiritish")
async def ask_project_content(message: Message, state: FSMContext):
    await state.set_state(ProjectState.waiting_content)
    await message.answer(
        "Loyihangiz haqida matn yuboring (link, tavsif va h.k.).\n"
        "Bekor qilish uchun \"❌ Bekor qilish\" tugmasini bosing.",
        reply_markup=kb.cancel_kb(),
    )


@router.message(ProjectState.waiting_content, F.text == "❌ Bekor qilish")
async def cancel_project(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=kb.user_main_menu())


@router.message(ProjectState.waiting_content)
async def receive_project(message: Message, state: FSMContext, bot: Bot):
    content = message.text or message.caption or ""
    project_id = db.add_project(message.from_user.id, content, auto_approve=False)
    await state.clear()
    await message.answer(
        "Loyihangiz adminga yuborildi, tasdiqlanishini kuting.",
        reply_markup=kb.user_main_menu(),
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🆕 Yangi loyiha so'rovi (ID: {project_id})\n"
                f"Yuboruvchi: {message.from_user.full_name} (id: {message.from_user.id})\n\n"
                f"{content}",
                reply_markup=kb.project_review_kb(project_id),
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("proj_approve:"))
async def approve_project(callback: CallbackQuery, bot: Bot):
    project_id = int(callback.data.split(":")[1])
    project = db.get_project(project_id)
    if not project:
        await callback.answer("Loyiha topilmadi.", show_alert=True)
        return

    db.set_project_status(project_id, "approved")
    await callback.message.edit_text(callback.message.text + "\n\n✅ Ruxsat etildi.")
    await callback.answer("Tasdiqlandi.")

    # egasiga xabar
    try:
        await bot.send_message(project["owner_id"], "✅ Loyihangiz tasdiqlandi va botga qo'shildi!")
    except Exception:
        pass

    # hammaga e'lon
    post_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(project["created_at"]))
    text = (
        f"🆕 Yangi loyiha qo'shildi!\n"
        f"👤 Muallif ID: {project['owner_id']}\n"
        f"🕒 Qo'yilgan vaqti: {post_time}\n\n"
        f"{project['content']}"
    )
    for user in db.get_all_users():
        try:
            await bot.send_message(user["chat_id"], text)
        except Exception:
            pass


@router.callback_query(F.data.startswith("proj_reject:"))
async def reject_project(callback: CallbackQuery, bot: Bot):
    project_id = int(callback.data.split(":")[1])
    project = db.get_project(project_id)
    if not project:
        await callback.answer("Loyiha topilmadi.", show_alert=True)
        return

    db.set_project_status(project_id, "rejected")
    await callback.message.edit_text(callback.message.text + "\n\n❌ Rad etildi.")
    await callback.answer("Rad etildi.")

    try:
        await bot.send_message(project["owner_id"], "❌ Loyihangiz rad etildi.")
    except Exception:
        pass


@router.message(F.text == "📁 Loyihalar")
async def list_projects(message: Message):
    projects = db.get_approved_projects()
    if not projects:
        await message.answer("Hozircha hech qanday loyiha yo'q.")
        return

    for p in projects[:20]:
        post_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(p["created_at"]))
        await message.answer(f"🕒 {post_time}\n\n{p['content']}")
