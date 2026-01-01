from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
import os
from modules import *



# Define a command handler for the /start command
@requires_access
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.update({
        "keyboard_markup": None,
        "can_type": True,
        "bot_reply_on_message": None,
        "last_bot_message_id": None,
        "chat_id": update.effective_chat.id,
        "callback": "script_and_description_generation"
    })
    await update.message.reply_text("Hi there. Please send your chosen story:")

# Define a message handler for text messages
@requires_access
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    await update.message.reply_text(user_id)

# Define a button handler for inline keyboard buttons
@requires_access
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