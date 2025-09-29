import json
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN, ADMIN_ID, CHANNEL
from utils import save_user

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Foydalanuvchilar ma'lumotlari
user_data = {}

# Savollarni yuklash
with open("questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)


# --- Kanalga obuna tekshirish ---
async def check_subscription(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# --- Start komandasi ---
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    subscribed = await check_subscription(message.from_user.id)
    if not subscribed:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔗 Kanalga obuna bo‘lish", url=f"https://t.me/{CHANNEL[1:]}"))
        markup.add(InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub"))
        await message.answer("❌ Botdan foydalanish uchun kanalga obuna bo‘ling.", reply_markup=markup)
        return

    # Ma'lumot yig‘ish
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
    await message.answer("Assalomu alaykum! Iltimos, telefon raqamingizni yuboring.", reply_markup=kb)


# --- Obuna tekshirish tugmasi ---
@dp.callback_query_handler(lambda c: c.data == "check_sub")
async def check_sub(call: types.CallbackQuery):
    subscribed = await check_subscription(call.from_user.id)
    if subscribed:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
        await call.message.answer("✅ Obuna tasdiqlandi! Endi telefon raqamingizni yuboring.", reply_markup=kb)
    else:
        await call.answer("❌ Hali obuna bo‘lmadingiz!", show_alert=True)


# --- Telefon raqamni olish ---
@dp.message_handler(content_types=["contact"])
async def get_contact(message: types.Message):
    user_data[message.from_user.id] = {
        "phone": message.contact.phone_number,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
        "score": 0
    }

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📘 Matematika", callback_data="subject_math"))
    kb.add(InlineKeyboardButton("📗 Ingliz tili", callback_data="subject_english"))
    await message.answer("✅ Ma'lumot olindi! Endi fan tanlang:", reply_markup=kb)


# --- Fan tanlash ---
@dp.callback_query_handler(lambda c: c.data.startswith("subject_"))
async def choose_subject(call: types.CallbackQuery):
    subject = call.data.split("_")[1]
    user_data[call.from_user.id]["subject"] = subject
    user_data[call.from_user.id]["q_index"] = 0
    await ask_question(call.from_user.id, call.message)


# --- Savol berish ---
async def ask_question(user_id, message):
    q_index = user_data[user_id]["q_index"]
    if q_index >= len(questions):
        score = user_data[user_id]["score"]
        subject = user_data[user_id]["subject"]
        first_name = user_data[user_id]["first_name"]
        last_name = user_data[user_id]["last_name"]
        phone = user_data[user_id]["phone"]

        save_user(user_id, first_name, last_name, phone, subject, score)
        await message.answer(f"✅ Test tugadi!\n\nNatijangiz: {score}/{len(questions)} ball")
        return

    q = questions[q_index]
    kb = InlineKeyboardMarkup()
    for opt in q["options"]:
        kb.add(InlineKeyboardButton(opt, callback_data=f"answer_{opt}"))
    await message.answer(q["question"], reply_markup=kb)


# --- Javoblarni tekshirish ---
@dp.callback_query_handler(lambda c: c.data.startswith("answer_"))
async def check_answer(call: types.CallbackQuery):
    user_id = call.from_user.id
    q_index = user_data[user_id]["q_index"]
    answer = call.data.split("_", 1)[1]

    if answer == questions[q_index]["answer"]:
        user_data[user_id]["score"] += 1

    user_data[user_id]["q_index"] += 1
    await ask_question(user_id, call.message)


# --- Admin uchun users.xlsx yuborish ---
@dp.message_handler(commands=["users"])
async def send_users(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer_document(open("users.xlsx", "rb"))
    else:
        await message.answer("❌ Siz admin emassiz!")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
