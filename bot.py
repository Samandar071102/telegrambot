import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from openpyxl import Workbook, load_workbook
import os

TOKEN = "BOT_TOKENINGIZNI_KIRITIN"   # BotFather dan olingan token
CHANNEL_ID = "@kanal_nomi"           # Kanal username

# Excel faylni yaratish
if not os.path.exists("users.xlsx"):
    wb = Workbook()
    ws = wb.active
    ws.append(["UserID", "Ism", "Familiya", "Telefon", "Qiziqishi"])
    wb.save("users.xlsx")

# Bot va dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Ma’lumotlarni vaqtincha saqlash
user_data = {}

# Start komandasi
@dp.message(Command("start"))
async def start(message: types.Message):
    member = await bot.get_chat_member(CHANNEL_ID, message.from_user.id)
    if member.status == "left":
        await message.answer("❗ Botdan foydalanish uchun kanalga obuna bo‘ling", 
                             reply_markup=types.InlineKeyboardMarkup(
                                 inline_keyboard=[
                                     [types.InlineKeyboardButton(text="📢 Kanalga obuna bo‘lish", url=f"https://t.me/{CHANNEL_ID[1:]}")]
                                 ]
                             ))
        return
    await message.answer("Assalomu alaykum! Ismingizni kiriting:")
    user_data[message.from_user.id] = {}

# Ism qabul qilish
@dp.message(lambda msg: msg.from_user.id in user_data and "ism" not in user_data[msg.from_user.id])
async def get_name(message: types.Message):
    user_data[message.from_user.id]["ism"] = message.text
    await message.answer("Familiyangizni kiriting:")

# Familiya
@dp.message(lambda msg: "ism" in user_data.get(msg.from_user.id, {}) and "familiya" not in user_data[msg.from_user.id])
async def get_surname(message: types.Message):
    user_data[message.from_user.id]["familiya"] = message.text
    await message.answer("Telefon raqamingizni kiriting:")

# Telefon
@dp.message(lambda msg: "familiya" in user_data.get(msg.from_user.id, {}) and "telefon" not in user_data[msg.from_user.id])
async def get_phone(message: types.Message):
    user_data[message.from_user.id]["telefon"] = message.text
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📐 Matematika"), KeyboardButton(text="🇬🇧 Ingliz tili")],
            [KeyboardButton(text="📖 Ona tili")]
        ],
        resize_keyboard=True
    )
    await message.answer("Qaysi fanga qiziqasiz?", reply_markup=kb)

# Qiziqish
@dp.message(lambda msg: "telefon" in user_data.get(msg.from_user.id, {}) and "fan" not in user_data[msg.from_user.id])
async def get_subject(message: types.Message):
    fan = message.text
    user_data[message.from_user.id]["fan"] = fan

    # Excelga yozish
    wb = load_workbook("users.xlsx")
    ws = wb.active
    ws.append([
        message.from_user.id,
        user_data[message.from_user.id]["ism"],
        user_data[message.from_user.id]["familiya"],
        user_data[message.from_user.id]["telefon"],
        user_data[message.from_user.id]["fan"]
    ])
    wb.save("users.xlsx")

    await message.answer(f"{fan} bo‘yicha testni boshlaymiz!")
    await send_test(message.from_user.id, fan)

# Test yuborish
async def send_test(user_id, fan):
    file_map = {
        "📐 Matematika": "tests/matematika.json",
        "🇬🇧 Ingliz tili": "tests/ingliz.json",
        "📖 Ona tili": "tests/ona_tili.json"
    }
    path = file_map.get(fan)
    if not path or not os.path.exists(path):
        await bot.send_message(user_id, "❌ Bu fan bo‘yicha test topilmadi.")
        return

    with open(path, "r", encoding="utf-8") as f:
        savollar = json.load(f)

    for s in savollar:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(*s["variantlar"])
        await bot.send_message(user_id, s["savol"], reply_markup=kb)

# Run
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
