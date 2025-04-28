import logging
import os
import time
import csv
import requests
from io import StringIO
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackContext

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Setup Google Sheet (Published CSV link)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSKd5gh5iOzsGtoFglkdqZ6WDah1dbYWYffNvRolpdvSF-UJ9EEB2HaT7EYSqv0l_k2wrlJRhpivOyO/pub?output=csv"

# Telegram Token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Simpan session user
user_session = {}  # {user_id: (session_active:bool, last_active_time:int)}

def should_reply(update):
    user_id = update.message.from_user.id
    text = update.message.text.lower() if update.message.text else ""
    current_time = time.time()

    if user_id in user_session:
        session_active, last_active = user_session[user_id]
        if current_time - last_active > 300:
            user_session[user_id] = (False, current_time)
            session_active = False
    else:
        session_active = False

    if session_active:
        if any(stop in text for stop in ["bye", "tq", "thank you", "terima kasih"]):
            user_session[user_id] = (False, current_time)
            return False
        user_session[user_id] = (True, current_time)
        return True

    if '@airasiaride_bot' in text or any(greet in text for greet in ["assalamualaikum", "salam", "hi", "hello"]):
        user_session[user_id] = (True, current_time)
        return True

    if update.message.sticker or (update.message.text and "👍" in update.message.text):
        user_session[user_id] = (True, current_time)
        return True

    return False

def get_sheet_data():
    response = requests.get(CSV_URL)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch sheet data: {response.text}")
    csv_data = response.content.decode('utf-8')
    f = StringIO(csv_data)
    reader = csv.DictReader(f)
    records = list(reader)
    return records

# Fungsi bila ada mesej
async def handle_message(update: Update, context: CallbackContext):
    try:
        if not should_reply(update):
            return

        text = update.message.text.lower() if update.message.text else ""
        print(f"[DEBUG] Incoming Message: {text}")

        records = get_sheet_data()
        replies = []

        for record in records:
            keyword = record.get('Keyword', '').lower()
            jawapan = record.get('Jawapan', '')

            if keyword and keyword in text:
                replies.append(jawapan)

        if replies:
            combined_reply = "\n\n".join(replies)
            await update.message.reply_text(combined_reply)
        else:
            await update.message.reply_text("...")

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        await update.message.reply_text("Maaf, ada masalah teknikal.")

# Run bot
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    print("🤖 Bot sudah mula jalan...")
    app.run_polling(stop_signals=None)

if __name__ == '__main__':
    main()
