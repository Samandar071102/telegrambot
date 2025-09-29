import os
import json
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("BOT_TOKEN")  # Render sozlamasida environment variable qilib qo'yasan
bot = Bot(token=TOKEN)
dp = Dispatcher()

app = Flask(__name__)

# Foydalanuvchi ma'lumotlari
user_data = {}

# Fanlar ro'yxati
subjects = ["📐 Matematika", "🇬🇧 Ingliz tili", "📖 Ona tili"]

# Start komandasi
@dp.message(Command("start"))
async def start(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer("Assalomu alaykum! Ismingizni kiriting:")

# Ism
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

# Qiziqish va test
@dp.message(lambda msg: "telefon" in user_data.get(msg.from_user.id, {}) and "fan" not in user_data[msg.from_user.id])
async def get_subject(message: types.Message):
    fan = message.text
    if fan not in subjects:
        await message.answer("Iltimos, tugmalar orqali fanni tanlang.")
        return

    user_data[message.from_user.id]["fan"] = fan

    await message.answer(f"{fan} bo‘yicha testni boshlaymiz!")
    await send_test(message.from_user.id, fan)

# Testni yuborish
async def send_test(user_id, fan):
    fan_map = {
        "📐 Matematika": "matematika",
        "🇬🇧 Ingliz tili": "ingliz tili",
        "📖 Ona tili": "ona tili"
    }

    subject_key = fan_map.get(fan)
    if not subject_key:
        await bot.send_message(user_id, "❌ Bu fan bo‘yicha test topilmadi.")
        return

    with open("tests.json", "r", encoding="utf-8") as f:
        tests = json.load(f)

    if subject_key not in tests:
        await bot.send_message(user_id, "❌ Testlar topilmadi.")
        return

    for s in tests[subject_key]:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(*s["variantlar"])
        await bot.send_message(user_id, s["savol"], reply_markup=kb)

# Flask webhook
@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = types.Update.model_validate(request.json)
    await dp.feed_update(bot, update)
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "✅ Bot ishlayapti!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
