import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Update
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "supersecret")
BASE_URL = os.getenv("BASE_URL")  # например: https://your-app.onrender.com
WEBHOOK_PATH = f"/webhook/{WEBHOOK_SECRET}"

if not BOT_TOKEN:
    raise RuntimeError("Не найден BOT_TOKEN. Создайте .env и укажите токен.")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
app = FastAPI(title="Telegram Webhook Bot")

@dp.message(CommandStart())
async def cmd_start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сказать привет", callback_data="hello")],
        [InlineKeyboardButton(text="Помощь", callback_data="help")]
    ])
    await message.answer("Привет! Я на вебхуке ✅", reply_markup=kb)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("Команды: /start, /help, /echo <текст>")

@dp.message(Command("echo"))
async def cmd_echo(message: Message):
    text = message.text.partition(" ")[2].strip()
    await message.answer(text or "Дай текст после /echo")

@dp.callback_query(F.data.in_({"hello", "help"}))
async def on_buttons(callback: CallbackQuery):
    if callback.data == "hello":
        await callback.message.answer("Привет с вебхука! 👋")
    else:
        await callback.message.answer("Это помощь: /help")
    await callback.answer()

@dp.message()
async def catch_all(message: Message):
    if message.text:
        await message.answer(f"Эхо: {message.text}")
    else:
        await message.answer("Понимаю только текст 🙂")

@app.on_event("startup")
async def on_startup():
    if BASE_URL:
        await bot.set_webhook(url=BASE_URL + WEBHOOK_PATH, allowed_updates=dp.resolve_used_update_types())
        logging.info("Webhook set to %s", BASE_URL + WEBHOOK_PATH)
    else:
        logging.warning("BASE_URL не задан, вебхук не будет установлен.")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})
