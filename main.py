from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
import os

state_store = {
    "chat_id": None,
    "user_id": None,
    "ui_state": "menu",
    "job": None
}

keyboard = [
    [InlineKeyboardButton("Services", callback_data="main:services")],
    [InlineKeyboardButton("Deploy", callback_data="main:deploy")],
    [InlineKeyboardButton("Status", callback_data="main:status")]
]

markup = InlineKeyboardMarkup(keyboard)

# Function to check if the user had access
def has_access(update):
    ALLOWED_USER_ID = os.getenv("ALLOWED_USER_ID")
    return update.effective_user.id == int(ALLOWED_USER_ID)

# Define a command handler for the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ui_state
    if not has_access(update):
        await update.message.reply_text('Access denied.')
        return

    state_store["ui_state"] = "menu"
    await update.message.reply_text('Hello! I am your friendly bot. How can I assist you today?', reply_markup=markup)

# Define a message handler for text messages
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_access(update):
        await update.message.reply_text('Access denied.')
        return
    user_id = update.effective_user.id
    user_message = update.message.text
    await update.message.reply_text(user_id)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "main:services":
        await query.edit_message_text(text="You selected Services.")
    elif data == "main:deploy":
        await query.edit_message_text(text="You selected Deploy.")
    elif data == "main:status":
        await query.edit_message_text(text="You selected Status.")

# Main function
def main():
    # Create the Application and pass it your bot's token
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    application = Application.builder().token(TOKEN).build()

    # Register the command handler
    application.add_handler(CommandHandler("start", start))
    # Register the message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    # Register the button handler
    application.add_handler(CallbackQueryHandler(button_handler))

    # Start the Bot
    application.run_polling(drop_pending_updates=True)



if __name__ == '__main__':
    main()