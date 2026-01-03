from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
import os, logging
from modules.modules_script_and_description_generation import *
from modules.modules_general import *

logger = logging.getLogger(__name__)
logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
# Suppress debug logs from external libraries
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Define a command handler for the /start command
@requires_access
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.update({
        "keyboard_markup": None,
        "can_type": True,
        "bot_reply_on_message": None,
        "chat_id": update.effective_chat.id,
        "on_message_callback": "script_and_description_generation",
        "on_button_callback": None,
        "section_storage": {
            "is_reviewed_script": False,
            "is_reviewed_description": False
        }
    })
    os.makedirs("story_data", exist_ok=True)

    await update.message.reply_text("Hi there. Please send your chosen story:")

# Define a message handler for text messages
@requires_access
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # GENERAL MESSAGE HANDLER
    callback = context.user_data.get("on_message_callback")
    if callback:
        await globals()[callback](update, context)
    elif not context.user_data.get("can_type"):
        await update.message.reply_text(context.user_data.get("bot_reply_on_message", "Please use /start to begin."), reply_markup=context.user_data.get("keyboard_markup"))
    else:
        await update.message.reply_text("Please use /start to begin.")

# Define a button handler for inline keyboard buttons
@requires_access
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(context.user_data)
    # GENERAL BUTTON HANDLER
    callback = context.user_data.get("on_button_callback")
    if callback:
        await globals()[callback](update, context)

# Main function
def main():
    logger.info("Starting bot...")
    # Create the Application and pass it your bot's token
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    application = Application.builder().token(TOKEN).build()

    # Register the command handler
    application.add_handler(CommandHandler("start", start))
    # Register the message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    # Register the button handler
    application.add_handler(CallbackQueryHandler(button_handler))

    # Start the Bot
    application.run_polling(drop_pending_updates=True)



if __name__ == '__main__':
    main()