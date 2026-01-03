from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
import os, logging
from functools import wraps
from openai import AsyncOpenAI
from json import loads, dumps

# A decorator to check if the user had access
def requires_access(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        ALLOWED_USER_ID = os.getenv("ALLOWED_USER_ID")
        if update.effective_user.id == int(ALLOWED_USER_ID):
            return await func(update, context, *args, **kwargs)
        else:
            if update.message:
                await update.message.reply_text('Access denied.')
            elif update.callback_query:
                await update.callback_query.answer('Access denied.', show_alert=True)
            return None
    return wrapper

# Function to split the output into more messages if it exceeds Telegram's limit
async def send_long_message(update, text, keyboard_markup=None):
    max_length = 4096
    for i in range(0, len(text), max_length):
        chunk = text[i:i + max_length]
        if update.message:
            await update.message.reply_text(chunk, reply_markup=keyboard_markup if i == 0 else None)
        elif update.callback_query:
            await update.callback_query.message.reply_text(chunk, reply_markup=keyboard_markup if i == 0 else None)

# Function to load contents of a file - TXT or JSON
def load_file_contents(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        if filepath.endswith(".json"):
            return loads(file.read())
        else:
            return file.read()

# Function to save contents to a file - TXT or JSON
def save_file_contents(filepath, content):
    with open(filepath, "w", encoding="utf-8") as file:
        if filepath.endswith(".json"):
            file.write(dumps(content, ensure_ascii=False, indent=4))
        else:
            file.write(content)