import os
import time
import json
import logging
import requests
from google.oauth2 import service_account
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackContext

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Google Sheets setup
SPREADSHEET_ID = '1-Rx-05zZ-Yj9znsuKPz827uXPZBflOfsSbBmpzNK2TY'
SHEET_NAME = 'Sheet1'
GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))

# Telegram Token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Session user
user_session = {}

# Create access token
def get_access_token():
    credentials = service_account.Credentials.from_service_account_info(
        GOOGLE_CREDENTIALS,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    access_token = credentials.token
    if not access_token or credentials.expired:
        credentials.refresh(requests.Request())
        access_token = credentials.token
    return access_token

# Fetch data from Google Sheet
def fetch_sheet_data():
    token = get_access_token()
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{SHEET_NAME}?alt=json"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    records = []
    values = data.get('values', [])
    headers_row = values[0] if values else []

    for row in values[1:]:
        record = {headers_row[i]: row[i] if i < len(row) else "" for i in range(len(headers_row))}
        records.append(record)

    return records

# Check need reply
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

# Handle incoming message
async def handle_message(update: Update, context: CallbackContext):
    if not should_reply(update):
        return

    text = update.message.text.lower() if update.message.text else ""
    records = fetch_sheet_data()
    replies = []

    for record in records:
        keyword = record.get('Keyword', '').lower()
        jawapan = record.get('Jawapan', '')

        if keyword in text:
            replies.append(jawapan)

    if replies:
        combined_reply = "\n\n".join(replies)
        await update.message.reply_text(combined_reply)
    else:
        await update.message.reply_text("...")

# Main
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    print("🤖 Bot sudah mula jalan...")
    app.run_polling(stop_signals=None)

if __name__ == '__main__':
    main()
