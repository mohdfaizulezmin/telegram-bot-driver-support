import logging
import gspread
import os
import time
import json
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackContext

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Setup Google Sheet
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_info = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))  # Ambil dari environment variable
credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_info, scope)
client = gspread.authorize(credentials)
sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1-Rx-05zZ-Yj9znsuKPz827uXPZBflOfsSbBmpzNK2TY/edit#gid=0')
worksheet = sheet.sheet1

# Telegram Token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Simpan session user
user_session = {}  # {user_id: (session_active:bool, last_active_time:int)}

# Fungsi untuk check perlu reply atau tidak
def should_reply(update):
    user_id = update.message.from_user.id
    text = update.message.text.lower() if update.message.text else ""
    current_time = time.time()

    # Auto-reset session jika lebih 5 minit tak aktif
    if user_id in user_session:
        session_active, last_active = user_session[user_id]
        if current_time - last_active > 300:  # 300 saat = 5 minit
            user_session[user_id] = (False, current_time)
            session_active = False
    else:
        session_active = False

    # Kalau user ada session aktif
    if session_active:
        # Check kalau user nak stop
        if any(stop in text for stop in ["bye", "tq", "thank you", "terima kasih"]):
            user_session[user_id] = (False, current_time)
            return False
        user_session[user_id] = (True, current_time)  # Update masa aktif
        return True

    # Kalau mesej teks ada salam atau nama bot
    if '@airasiaride_bot' in text or any(greet in text for greet in ["assalamualaikum", "salam", "hi", "hello"]):
        user_session[user_id] = (True, current_time)
        return True

    # Kalau mesej adalah sticker atau emoji thumbs up 👍
    if update.message.sticker or (update.message.text and "👍" in update.message.text):
        user_session[user_id] = (True, current_time)
        return True

    return False  # Kalau bukan, jangan reply

# Fungsi bila ada mesej
async def handle_message(update: Update, context: CallbackContext):
    if not should_reply(update):
        return

    text = update.message.text.lower() if update.message.text else ""

    # Baca semua rekod dari sheet
    records = worksheet.get_all_records()
    replies = []

    for record in records:
        keyword = record['Keyword'].lower()
        jawapan = record['Jawapan']

        if keyword in text:
            replies.append(jawapan)

    if replies:
        combined_reply = "\n\n".join(replies)  # Combine semua jawapan dengan newline antara setiap reply
        await update.message.reply_text(combined_reply)
    else:
        await update.message.reply_text("...")

# Run bot
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    print("🤖 Bot sudah mula jalan...")
    app.run_polling(stop_signals=None)

if __name__ == '__main__':
    main()
