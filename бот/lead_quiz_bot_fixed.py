import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, FSInputFile
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))  # пример: -5064332864
if not BOT_TOKEN:
    raise RuntimeError("Укажите BOT_TOKEN в .env")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- Ростов-на-Дону — преднастройки ---
AREAS = ["Центр", "Северный", "Западный", "Суворовский", "Левенцовка", "Военвед", "Не важно"]
TYPES = ["Квартира (новостройка)", "Квартира (вторичка)", "Дом", "Таунхаус", "Коммерция"]
BUDGETS = ["до 3 млн", "3–5 млн", "5–10 млн", "10–20 млн", "20–40 млн", "40+ млн", "Пока не знаю"]
ROOMS = ["Студия", "1", "2", "3+", "Не важно"]
TIMEFRAMES = ["Как можно скорее", "В этом месяце", "1–3 месяца", "Смотрю варианты"]
MORTGAGE = ["Есть одобрение", "Планирую/нужна консультация", "Наличные"]

class LeadQuiz(StatesGroup):
    purpose = State()
    area = State()
    type_ = State()
    budget = State()
    rooms = State()
    timeframe = State()
    mortgage = State()
    name = State()
    phone = State()

def ikb(options, prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=o, callback_data=f"{prefix}:{o}")] for o in options]
    )

async def ask_next(target, text: str, kb: InlineKeyboardMarkup):
    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=kb)
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb)

def summary(data: dict) -> str:
    return (
        "📝 Заявка — АН Welcome Day / Форсаж\n"
        f"• Цель: {data.get('purpose')}\n"
        f"• Район: {data.get('area')}\n"
        f"• Тип: {data.get('type_')}\n"
        f"• Бюджет: {data.get('budget')}\n"
        f"• Комнат: {data.get('rooms')}\n"
        f"• Срок: {data.get('timeframe')}\n"
        f"• Финансирование: {data.get('mortgage')}\n"
        f"• Имя: {data.get('name')}\n"
        f"• Телефон: {data.get('phone')}\n"
        f"• TG: @{data.get('tg')}"
    )

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    # Telegram требует, чтобы пользователь сам начал диалог, поэтому старт после /start
    await state.clear()
    await state.update_data(tg=message.from_user.username or "—")

    # Логотип (если файл лежит рядом в assets/logo.jpeg)
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.jpeg")
    caption = (
        "🏡 <b>АН Welcome Day / Форсаж</b>\n"
        "Подберём недвижимость в Ростове-на-Дону.\n"
        "Ответьте на несколько вопросов — займёт 30–60 секунд."
    )
    if os.path.exists(logo_path):
        await message.answer_photo(photo=FSInputFile(logo_path), caption=caption, parse_mode="HTML")
    else:
        await message.answer(caption, parse_mode="HTML")

    # Автостарт опроса
    await state.set_state(LeadQuiz.purpose)
    await message.answer("1) Какая цель?", reply_markup=ikb(["Купить", "Снять", "Инвестиции"], "purpose"))

@dp.callback_query(F.data.startswith("purpose:"))
async def q_purpose(cb: CallbackQuery, state: FSMContext):
    await state.update_data(purpose=cb.data.split(":", 1)[1])
    await state.set_state(LeadQuiz.area)
    await ask_next(cb, "2) Предпочтительный район?", ikb(AREAS, "area"))

@dp.callback_query(F.data.startswith("area:"))
async def q_area(cb: CallbackQuery, state: FSMContext):
    await state.update_data(area=cb.data.split(":", 1)[1])
    await state.set_state(LeadQuiz.type_)
    await ask_next(cb, "3) Тип недвижимости?", ikb(TYPES, "type"))

@dp.callback_query(F.data.startswith("type:"))
async def q_type(cb: CallbackQuery, state: FSMContext):
    await state.update_data(type_=cb.data.split(":", 1)[1])
    await state.set_state(LeadQuiz.budget)
    await ask_next(cb, "4) Бюджет?", ikb(BUDGETS, "budget"))

@dp.callback_query(F.data.startswith("budget:"))
async def q_budget(cb: CallbackQuery, state: FSMContext):
    await state.update_data(budget=cb.data.split(":", 1)[1])
    await state.set_state(LeadQuiz.rooms)
    await ask_next(cb, "5) Количество комнат?", ikb(ROOMS, "rooms"))

@dp.callback_query(F.data.startswith("rooms:"))
async def q_rooms(cb: CallbackQuery, state: FSMContext):
    await state.update_data(rooms=cb.data.split(":", 1)[1])
    await state.set_state(LeadQuiz.timeframe)
    await ask_next(cb, "6) Когда планируете сделку/переезд?", ikb(TIMEFRAMES, "timeframe"))

@dp.callback_query(F.data.startswith("timeframe:"))
async def q_timeframe(cb: CallbackQuery, state: FSMContext):
    await state.update_data(timeframe=cb.data.split(":", 1)[1])
    await state.set_state(LeadQuiz.mortgage)
    await ask_next(cb, "7) Финансирование?", ikb(MORTGAGE, "mortgage"))

@dp.callback_query(F.data.startswith("mortgage:"))
async def q_mortgage(cb: CallbackQuery, state: FSMContext):
    await state.update_data(mortgage=cb.data.split(":", 1)[1])
    await state.set_state(LeadQuiz.name)
    await cb.message.answer("8) Представьтесь, пожалуйста (имя).")
    await cb.answer()

@dp.message(LeadQuiz.name, F.text.len() > 0)
async def q_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(LeadQuiz.phone)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить номер", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer("9) Укажите телефон (кнопкой ниже или напишите номер):", reply_markup=kb)

@dp.message(LeadQuiz.phone, F.contact)
async def q_phone_contact(message: Message, state: FSMContext):
    await finish_lead(message, state, message.contact.phone_number)

@dp.message(LeadQuiz.phone, F.text.len() > 0)
async def q_phone_text(message: Message, state: FSMContext):
    await finish_lead(message, state, message.text.strip())

async def finish_lead(message: Message, state: FSMContext, phone: str):
    await state.update_data(phone=phone)
    data = await state.get_data()
    text = summary(data)

    await message.answer("Спасибо! Менеджер свяжется с вами в ближайшее время ✅", reply_markup=None)

    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(ADMIN_CHAT_ID, text)
        except Exception as e:
            logging.warning("Не удалось отправить лид админу: %s", e)

    await message.answer(text.replace("📝", "📋"))
    await state.clear()

@dp.message()
async def fallback(message: Message):
    await message.answer("Введите /start, чтобы начать подбор объекта 🙂")

if __name__ == "__main__":
    import asyncio
    async def main():
        await dp.start_polling(bot)
    asyncio.run(main())
