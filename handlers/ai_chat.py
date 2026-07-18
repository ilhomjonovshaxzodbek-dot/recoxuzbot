from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL
import database as db
import keyboards as kb

router = Router()
groq_client = Groq(api_key=GROQ_API_KEY)


class AIChatState(StatesGroup):
    chatting = State()


def build_system_prompt() -> str:
    """AI ga tizim prompti - tasdiqlangan loyihalarni tabiiy tarzda tavsiya qilishi uchun."""
    projects = db.get_approved_projects()
    if projects:
        projects_text = "\n".join(f"- {p['content'][:200]}" for p in projects[:10])
    else:
        projects_text = "Hozircha loyihalar yo'q."

    return (
        "Sen do'stona, samimiy AI suhbatdoshsan. Foydalanuvchi bilan erkin tilda gaplash. "
        "Agar mavzu mos kelsa, quyidagi loyihalardan birini tabiiy tarzda, majburlamasdan tavsiya qilishing mumkin:\n"
        f"{projects_text}\n"
        "Tavsiyani zo'rlab emas, suhbat oqimiga mos kelganda taklif qil."
    )


@router.message(F.text == "🤖 AI bilan suhbat")
async def start_ai_chat(message: Message, state: FSMContext):
    await state.set_state(AIChatState.chatting)
    await state.update_data(history=[])
    await message.answer(
        "AI bilan suhbat boshlandi. Chiqish uchun \"❌ Bekor qilish\" tugmasini bosing.",
        reply_markup=kb.cancel_kb(),
    )


@router.message(AIChatState.chatting, F.text == "❌ Bekor qilish")
async def stop_ai_chat(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Suhbat tugadi.", reply_markup=kb.user_main_menu())


@router.message(AIChatState.chatting)
async def ai_chat_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    history = data.get("history", [])

    history.append({"role": "user", "content": message.text})
    # tarixni oxirgi 10 xabar bilan cheklaymiz
    history = history[-10:]

    messages = [{"role": "system", "content": build_system_prompt()}] + history

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
        )
        reply_text = completion.choices[0].message.content
    except Exception:
        reply_text = "Kechirasiz, hozir javob bera olmadim. Birozdan so'ng qayta urinib ko'ring."

    history.append({"role": "assistant", "content": reply_text})
    await state.update_data(history=history)

    await message.answer(reply_text)
