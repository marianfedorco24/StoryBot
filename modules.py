from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
import os
from functools import wraps
from openai import OpenAI

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

#             Story Bot FUNCTION CHAIN

# Function to regenerate the inputted story and create a script with a description
def script_and_description_generation(user_story: str):
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    INSTRUCTIONS = """### ROLE
You are a master film director and storyboard writer. Your task is to rewrite a provided story into a script suitable for a viral video, split into 8-12 distinct scenes.

### ANALYSIS PHASE
Before writing, determine the overarching **GENRE and MOOD** of the story (e.g., Horror, Comedy, Fairy Tale, Noir).
- This mood is the "Visual Anchor."
- You must apply this mood to the lighting, color palette, and atmosphere of EVERY image description to ensure visual consistency.
- Example: If the story is Horror, EVERY image prompt must specify "dark, ominous lighting, scary atmosphere, muted colors."

### WRITING STYLE (STORY SECTIONS)
- Tone: Folksy, conversational, and natural. Like a friend telling a legend to a friend.
- Language: Simple and modern. No complex words.
- Format: Optimized for Text-to-Speech (TTS). It must sound good when read aloud. Do not use newlines, line breaks, or the newline character (\n).
- Structure:
  - Scene 1 MUST be a "Hook/Intro" (e.g., "Did you know that...", or a cliffhanger summary) to grab attention.
  - The following scenes tell the actual story chronologically.

### VISUAL STYLE (IMAGE PROMPTS)
- Style: Cartoony, but heavily influenced by the [Visual Anchor] determined above.
- Content: Describe the scene, setting, and characters.
- CRITICAL CONSTRAINT: Image generation is STATELESS. You must fully re-describe every character and setting in every single prompt.
  - NEVER use references like "the same man" or "him".
  - ALWAYS copy-paste the full visual details: Age, Hair, Clothes, Body, Face.
  - ALWAYS explicitly repeat the mood/lighting (e.g., "scary horror atmosphere") in every single prompt.
  - Characters must have exaggerated emotional expressions matching the story mood.

### OUTPUT FORMAT
Return ONLY raw JSON. Do not use Markdown formatting (no ```json). Do not add conversational filler.
The output must be a list of objects with this schema:
[
  {
    "story_section": "The narrated text for this scene...",
    "scene_image_description": "A cartoony illustration of [Character Name, full visual description] standing in [Setting, full description], [Specific Mood/Lighting adjectives]..."
  }
]
"""
    
    # ChatGPT API call to generate the script with image descriptions and video description
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.responses.create(
        model="gpt-5.2",
        input=user_story,
        instructions=INSTRUCTIONS,
    )

    print(response.output_text)

script_and_description_generation("df")