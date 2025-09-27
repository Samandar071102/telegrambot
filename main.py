import os
import telebot
from flask import Flask, request
import pandas as pd
from datetime import datetime

# ===============================
# TOKEN va Kanal ID
# ===============================
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Render.com'ga BOT_TOKEN sifatida qo'yamiz
CHANNEL_ID = "@aqllilik_balosi"          # Kanal username yoki ID (-100... bo'lsa ham yozsa bo'ladi)
EXCEL_FILE = "users.xlsx"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ===============================
# Excel faylni tayyorlash
# ===============================
if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=["user_id", "username", "first_name", "date"])
    df.to_excel(EXCEL_FILE, index=False)

def save_user(user_id, username, first_name):
    df = pd.read_excel(EXCEL_FILE)
    if user_id not in df["user_id"].values:
        new_user = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
        df.to_excel(EXCEL_FILE, index=False)

# ===============================
# Kanal obuna tekshirish
# ===============================
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except:
        return False

# ===============================
# Bot komandalar
# ===============================
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    if check_subscription(user_id):
        save_user(user_id, username, first_name)
        bot.reply_to(message, f"👋 Salom, {first_name}!\nSiz botga muvaffaqiyatli ulandingiz ✅")
    else:
        bot.reply_to(message,
            f"❌ Botdan foydalanish uchun avval kanalimizga obuna bo‘ling:\n{CHANNEL_ID}")

@bot.message_handler(commands=["sendall"])
def sendall(message):
    if message.from_user.id == 1130602920:  # Admin ID
        text = message.text.replace("/sendall ", "")
        df = pd.read_excel(EXCEL_FILE)
        for _, row in df.iterrows():
            try:
                bot.send_message(int(row["user_id"]), text)
            except:
                pass
        bot.reply_to(message, "✅ Xabar barcha foydalanuvchilarga yuborildi!")
    else:
        bot.reply_to(message, "❌ Siz admin emassiz!")

# ===============================
# Flask uchun webhook
# ===============================
@app.route("/" + BOT_TOKEN, methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Bot ishlayapti ✅", 200

# ===============================
# Render uchun ishga tushirish
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
