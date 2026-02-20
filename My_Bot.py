import asyncio
import os

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
API_URL = "http://127.0.0.1:8000"

my_bot = Bot(token=API_TOKEN)

disp = Dispatcher()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Add task"), KeyboardButton(text="List tasks")],
    ],
    resize_keyboard=True
)


@disp.message(CommandStart())
async def hello_button(msg: Message):
    await msg.answer("Привіт. Я бот для створення списку задач", reply_markup=main_keyboard)

@disp.message(lambda m: m.text == "Add task")
async def add_task(msg: Message):
    await msg.answer("Введи назву задачі")

@disp.message(lambda m: m.text not in ["Add task", "List tasks"])
async def process_task(msg: Message):
    async with aiohttp.ClientSession() as session:
        payload = {
            "id": hash(msg.text) % 10000,
            "title": msg.text,
            "status": "new"
        }
        async with session.post(f"{API_URL}/tasks", json=payload) as resp:
            if resp.status == 200:
                await msg.answer("Задачу додано")
            else:
                error_text = await resp.text()
                await msg.answer(f"Помилка при додаванні\n{error_text}")

@disp.message(lambda m: m.text == "List tasks")
async def list_tasks(msg: Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/tasks") as resp:
            tasks = await resp.json()
            if tasks:
                for t in tasks:
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="Завершити", callback_data=f"done_{t['id']}")],
                        [InlineKeyboardButton(text="Редагувати", callback_data=f"edit_{t['id']}")],
                        [InlineKeyboardButton(text="Видалити", callback_data=f"delete_{t['id']}")]
                    ])
                    await msg.answer(f"{t['id']}: {t['title']} ({t['status']})", reply_markup=kb)
            else:
                await msg.answer("Список задач порожній.")


@disp.callback_query(lambda c: c.data.startswith("done_"))
async def mark_done(callback: types.CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    async with aiohttp.ClientSession() as session:
        async with session.put(f"{API_URL}/tasks/{task_id}?status=done") as resp:
            if resp.status == 200:
                await callback.message.edit_text(f"Задачу {task_id} завершено")
            else:
                await callback.answer("Помилка при оновленні")

@disp.callback_query(lambda c: c.data.startswith("delete_"))
async def delete_task(callback: types.CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{API_URL}/tasks/{task_id}") as resp:
            if resp.status == 200:
                await callback.message.edit_text(f"Задачу {task_id} видалено")
            else:
                await callback.answer("Помилка при видаленні")


edit_buffer = {}  # тимчасове сховище для ID задачі, яку редагуємо

@disp.callback_query(lambda c: c.data.startswith("edit_"))
async def edit_task(callback: types.CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    edit_buffer[callback.from_user.id] = task_id
    await callback.message.answer(f"Введи нову назву для задачі {task_id}:")
    await callback.answer()

@disp.message()
async def handle_edit(msg: Message):
    if msg.from_user.id in edit_buffer:
        task_id = edit_buffer.pop(msg.from_user.id)
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{API_URL}/tasks/{task_id}?status=new", json={"title": msg.text}) as resp:
                if resp.status == 200:
                    await msg.answer(f"Задачу {task_id} оновлено: {msg.text}")
                else:
                    await msg.answer("Помилка при редагуванні")


async def start_bot():
    await disp.start_polling(my_bot)

asyncio.run(start_bot())