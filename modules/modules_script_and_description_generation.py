from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
import os, logging
from functools import wraps
from openai import AsyncOpenAI
from json import loads, dumps
from modules.modules_general import *

logger = logging.getLogger(__name__)

load_dotenv()

# ------------------ Story Bot FUNCTION CHAIN ------------------
# Function to regenerate the inputted story and create a script with a description
async def script_and_description_generation(update, context, regeneration=False):
    logger.info("SCRIPT AND DESCRIPTION GENERATION CALLED")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    INSTRUCTIONS = load_file_contents("prompts/script_and_description_generation_instructions.txt")
    
    user_story = ""
    if not regeneration:
        user_story = update.message.text
        save_file_contents("story_data/user_story.txt", user_story)
    else:
        user_story = load_file_contents("story_data/user_story.txt")

    # Acknowledge receipt of the story
    if update.message:
        await update.message.reply_text("Generating story script and video description from your input...\nThis may take a moment, please wait.")
    else:
        await update.callback_query.message.reply_text("Generating story script and video description from your input...\nThis may take a moment, please wait.")

    # ChatGPT API call to generate the script with image descriptions and video description
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    try:
        response = await client.responses.create(
            model="gpt-5.2",
            input=user_story,
            instructions=INSTRUCTIONS,
            temperature=0.7
        )
        script_and_description = response.output_text

        with open("story_data/script_and_description.json", "w", encoding="utf-8") as f:
            f.write(script_and_description)

    except Exception as e:
        await update.message.reply_text(f"An error occurred while generating the script: {e}")
        return
    # Update user data and send the generated output

    context.user_data.update({
        "section_storage": {
            "is_reviewed_script": False,
            "is_reviewed_description": False
        }
    })
    await review_script_or_description(update, context, location="default")

async def review_script_or_description(update, context, location=None):
    logger.info("REVIEW SCRIPT OR DESCRIPTION CALLED")
    if location == "default":
        keyboard_rows = []
        if not context.user_data["section_storage"]["is_reviewed_script"]:
            keyboard_rows.append([InlineKeyboardButton("Review the script", callback_data="review:script")])
        if not context.user_data["section_storage"]["is_reviewed_description"]:
            keyboard_rows.append([InlineKeyboardButton("Review the video description", callback_data="review:description")])

        if not keyboard_rows:
            #BOTH REVIEWED, CONTINUE --------------------------------------------------------------------------
            if update.message:
                await update.message.reply_text(text="BOTH REVIEWED")
            else:
                await update.callback_query.message.reply_text(text="BOTH REVIEWED")
        else:
            keyboard_markup = InlineKeyboardMarkup(keyboard_rows)
            context.user_data.update({
                "keyboard_markup": keyboard_markup,
                "can_type": False,
                "bot_reply_on_message": "Please review the generated script and video description.",
                "on_message_callback": None,
                "on_button_callback": "review_script_or_description"
            })
            if update.message:
                await update.message.reply_text("Done!\nStory has been rewritten, image descriptions have been generated, and video description created.\nPlease review them:", reply_markup=keyboard_markup)
            elif update.callback_query:
                await update.callback_query.message.reply_text("Done!\nStory has been rewritten, image descriptions have been generated, and video description created.\nPlease review them:", reply_markup=keyboard_markup)
    else:
        query = update.callback_query
        await query.answer()
        data = query.data
        script_and_description = load_file_contents("story_data/script_and_description.json")

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
    logger.info("REVIEW SCRIPT CALLED")         
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "review:script:confirm":
        context.user_data["section_storage"]["is_reviewed_script"] = True
        await query.message.reply_text(text="You have confirmed the script.")
        await review_script_or_description(update, context, location="default")
    elif data == "review:script:regenerate":
        # LOAD IT FROM THE FILE AND PASS IT TO THE FUNCTION
        await script_and_description_generation(update, context, regeneration=True)

async def review_description(update, context):
    logger.info("REVIEW DESCRIPTION CALLED")
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "review:description:confirm":
        context.user_data["section_storage"]["is_reviewed_description"] = True
        await query.message.reply_text(text="You have confirmed the video description.")
        await review_script_or_description(update, context, location="default")
    elif data == "review:description:edit":
        context.user_data.update({
            "keyboard_markup": None,
            "can_type": True,
            "bot_reply_on_message": None,
            "on_message_callback": "edit_description",
            "on_button_callback": None
        })
        await query.message.reply_text(text="Please enter the new video description:")

async def edit_description(update, context):
    logger.info("EDIT DESCRIPTION CALLED")
    new_description = update.message.text
    script_and_description = load_file_contents("story_data/script_and_description.json")
    script_and_description["video_description"] = new_description
    save_file_contents("story_data/script_and_description.json", script_and_description)

    await update.message.reply_text("Video description updated successfully.")
    context.user_data["section_storage"]["is_reviewed_description"] = True
    await review_script_or_description(update, context, location="default")