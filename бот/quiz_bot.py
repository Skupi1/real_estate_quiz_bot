import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Укажите BOT_TOKEN в .env")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

QUIZ = [
    {
        "question": "Какая планета ближе всего к Солнцу?",
        "options": ["Меркурий", "Венера", "Земля", "Марс"],
        "correct": 0
    },
    {
        "question": "Сколько будет 7 × 8?",
        "options": ["54", "56", "58", "64"],
        "correct": 1
    },
    {
        "question": "Кто написал 'Войну и мир'?",
        "options": ["Пушкин", "Толстой", "Достоевский", "Гоголь"],
        "correct": 1
    },
    {
        "question": "Какой язык программирования чаще всего используют для Telegram-ботов?",
        "options": ["C++", "Python", "Java", "Go"],
        "correct": 1
    },
]

class Quiz(StatesGroup):
    question = State()
    score = State()

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(Quiz.question)
    await state.update_data(score=0, index=0)
    await send_question(message, state)

async def send_question(message_or_cb, state: FSMContext):
    data = await state.get_data()
    index = data.get("index", 0)

    if index >= len(QUIZ):
        score = data.get("score", 0)
        await state.clear()
        await message_or_cb.answer(
            f"✅ Квиз завершён!\nПравильных ответов: {score} из {len(QUIZ)}.\n\n"
            "Нажми /start, чтобы сыграть ещё раз."
        )
        return

    q = QUIZ[index]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=opt, callback_data=f"answer_{i}")] for i, opt in enumerate(q["options"])]
    )
    await message_or_cb.answer(f"❓ Вопрос {index + 1}/{len(QUIZ)}:\n\n{q['question']}", reply_markup=kb)

@dp.callback_query(F.data.startswith("answer_"))
async def process_answer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data.get("index", 0)
    q = QUIZ[index]

    answer_index = int(callback.data.split("_")[1])
    correct_index = q["correct"]

    if answer_index == correct_index:
        await callback.answer("✅ Правильно!", show_alert=False)
        data["score"] += 1
    else:
        await callback.answer(f"❌ Неправильно! Правильный ответ: {q['options'][correct_index]}", show_alert=True)

    data["index"] += 1
    await state.update_data(score=data["score"], index=data["index"])
    await send_question(callback.message, state)

if __name__ == "__main__":
    import asyncio
    async def main():
        await dp.start_polling(bot)
    asyncio.run(main())
