import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Не найден BOT_TOKEN. Создайте файл .env на основе .env.example и укажите токен.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сказать привет", callback_data="hello")],
        [InlineKeyboardButton(text="Помощь", callback_data="help")]
    ])
    await message.answer("Привет! Я живой 😊 Нажми кнопку или напиши /help", reply_markup=kb)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("Команды:\n/start — начать\n/help — помощь\n/echo <текст> — повторю ваш текст")

@dp.message(Command("echo"))
async def cmd_echo(message: Message):
    text = message.text.partition(" ")[2].strip()
    await message.answer(text or "Дай текст после /echo")

@dp.callback_query(F.data == "hello")
async def on_hello(callback: CallbackQuery):
    await callback.message.answer("Привет-привет! 👋")
    await callback.answer()

@dp.callback_query(F.data == "help")
async def on_help(callback: CallbackQuery):
    await callback.message.answer("Это помощь: /help")
    await callback.answer()

@dp.message()
async def catch_all(message: Message):
    if message.text:
        await message.answer(f"Ты написал: {message.text}")
    else:
        await message.answer("Я понимаю только текстовые сообщения пока что 🙂")

if __name__ == "__main__":
    import asyncio
    async def main():
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    asyncio.run(main())
