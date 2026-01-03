from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
import os, logging
from functools import wraps
from openai import AsyncOpenAI
from json import loads, dumps

logger = logging.getLogger(__name__)
logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
# Suppress debug logs from external libraries
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
load_dotenv()

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

# Helper function to load instructions efficiently
def load_instructions(filepath="chatgpt_instructions.txt"):
    with open(filepath, "r", encoding="utf-8") as file:
        return file.read()

# ------------------ Story Bot FUNCTION CHAIN ------------------
# Function to regenerate the inputted story and create a script with a description
async def script_and_description_generation(update, context, regeneration_story=None):
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    INSTRUCTIONS = load_instructions()
    
    user_story = ""
    if regeneration_story:
        user_story = regeneration_story
    else:
        user_story = update.message.text
    context.user_data["user_story"] = user_story

    # Acknowledge receipt of the story
    await update.message.reply_text("Generating story script and video description from your input...\nThis may take a moment, please wait.")

    # ChatGPT API call to generate the script with image descriptions and video description
    # client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    # try:
    #     response = await client.responses.create(
    #         model="gpt-5.2",
    #         input=user_story,
    #         instructions=INSTRUCTIONS,
    #         temperature=0.7
    #     )
    #     script_and_description = response.output_text

    #     with open("story_data/script_and_description.json", "w", encoding="utf-8") as f:
    #         f.write(script_and_description)

    # except Exception as e:
    #     await update.message.reply_text(f"An error occurred while generating the script: {e}")
    #     return
    # Update user data and send the generated output
    keyboard_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Review the script", callback_data="review:script")],
        [InlineKeyboardButton("Review the video description", callback_data="review:description")]
        ])
    context.user_data.update({
        "keyboard_markup": keyboard_markup,
        "can_type": False,
        "bot_reply_on_message": "Please review the generated script and video description.",
        "chat_id": update.effective_chat.id,
        "on_message_callback": None,
        "on_button_callback": "review_script_or_description",
        "section_storage": {
            "is_reviewed_script": False,
            "is_reviewed_description": False
        }
    })
    await update.message.reply_text("Done!\nStory has been rewritten, image descriptions have been generated, and video description created.\nPlease review them:", reply_markup=keyboard_markup)
    

async def review_script_or_description(update, context, location=None):
    logger.info("REVIEW SCRIPT OR DESCRIPTION CALLED")
    query = update.callback_query
    await query.answer()
    data = query.data

    if location == "default":
        keyboard_rows = []
        if not context.user_data["section_storage"]["is_reviewed_script"]:
            keyboard_rows.append([InlineKeyboardButton("Review the script", callback_data="review:script")])
        if not context.user_data["section_storage"]["is_reviewed_description"]:
            keyboard_rows.append([InlineKeyboardButton("Review the video description", callback_data="review:description")])

        if not keyboard_rows:
            #BOTH REVIEWED, CONTINUE --------------------------------------------------------------------------
            await query.message.reply_text(text="BOTH REVIEWED")
        else:
            keyboard_markup = InlineKeyboardMarkup(keyboard_rows)
            if update.message:
                await update.message.reply_text("Done!\nStory has been rewritten, image descriptions have been generated, and video description created.\nPlease review them:", reply_markup=keyboard_markup)
            elif update.callback_query:
                await query.message.reply_text("Done!\nStory has been rewritten, image descriptions have been generated, and video description created.\nPlease review them:", reply_markup=keyboard_markup)
    else:
        script_and_description = ""
        with open("story_data/script_and_description.json", "r", encoding="utf-8") as f:
            script_and_description = loads(f.read())

        if data == "review:script":
            keyboard_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Confirm", callback_data="review:script:confirm")],
            [InlineKeyboardButton("Regenerate the script and video description", callback_data="review:script:regenerate")]
            ])
            context.user_data.update({
            "keyboard_markup": keyboard_markup,
            "can_type": False,
            "bot_reply_on_message": "Please review the generated script.",
            "on_message_callback": None,
            "on_button_callback": "review_script"
        })
            await send_long_message(update, dumps(script_and_description["script"], indent=2, ensure_ascii=False), keyboard_markup)
        elif data == "review:description":
            keyboard_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Confirm", callback_data="review:description:confirm")],
            [InlineKeyboardButton("Edit the video description", callback_data="review:description:edit")]
            ])
            context.user_data.update({
            "keyboard_markup": keyboard_markup,
            "can_type": False,
            "bot_reply_on_message": "Please review the generated video description.",
            "on_message_callback": None,
            "on_button_callback": "review_description"
        })
            await query.message.reply_text(text=script_and_description["video_description"], reply_markup=keyboard_markup)

async def review_script(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "review:script:confirm":
        context.user_data["section_storage"]["is_reviewed_script"] = True
        await query.message.reply_text(text="You have confirmed the script.")
        await review_script_or_description(update, context, location="default")
    elif data == "review:script:regenerate":
        await script_and_description_generation(update, context, regeneration_story=context.user_data["user_story"])

async def review_description(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "review:description:confirm":
        context.user_data["section_storage"]["is_reviewed_description"] = True
        await query.message.reply_text(text="You have confirmed the video description.")
        await review_script_or_description(update, context, location="default")
    elif data == "review:description:regenerate":
        pass
        # Implement editing functionality if needed