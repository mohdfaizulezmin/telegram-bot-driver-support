import logging
import os
import time
import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackContext

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Setup Google Sheet
GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
SPREADSHEET_ID = "1-Rx-05zZ-Yj9znsuKPz827uXPZBflOfsSbBmpzNK2TY"
SHEET_NAME = "Sheet1"

def get_access_token():
    credentials = service_account.Credentials.from_service_account_info(
        GOOGLE_CREDENTIALS,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    if not credentials.valid or credentials.expired:
        credentials.refresh(Request())
    return credentials.token

def get_sheet_data():
    access_token = get_access_token()
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{SHEET_NAME}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch sheet data: {response.text}")
    data = response.json()
    values = data.get("values", [])
    if not values:
        return []
    headers = values[0]
    records = [dict(zip(headers, row)) for row in values[1:]]
    return records

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
