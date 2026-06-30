"""
🌐 Lingua Swap Bot - Professional Language Translator
Translate text between multiple languages with auto-detection and pronunciation
"""

import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Try to import googletrans for real translation
try:
    from googletrans import Translator, LANGUAGES
    REAL_TRANSLATION = True
except ImportError:
    REAL_TRANSLATION = False
    print("⚠️ googletrans not installed. Using fallback translation.")

# ==================== LOGGING ====================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================

# Try multiple possible token variable names
BOT_TOKEN = (
    os.environ.get("TELEGRAM_TOKEN") or
    os.environ.get("TELEGRAM_BOT_TOKEN") or
    os.environ.get("BOT_TOKEN")
)

# If token is not set, try reading from .env file
if not BOT_TOKEN:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        BOT_TOKEN = (
            os.environ.get("TELEGRAM_TOKEN") or
            os.environ.get("TELEGRAM_BOT_TOKEN") or
            os.environ.get("BOT_TOKEN")
        )
    except:
        pass

# If still no token, show error
if not BOT_TOKEN:
    logger.error("=" * 60)
    logger.error("❌ ERROR: No Telegram Bot Token found!")
    logger.error("=" * 60)
    raise ValueError("❌ No Telegram Bot Token found in environment variables!")

BOT_NAME = "Lingua Swap Bot"
BOT_USERNAME = "lingua_swap_bot"
BOT_VERSION = "1.0.0"

# ==================== LANGUAGE DATA ====================

# Language codes with names and flags
LANG_CODES = {
    "en": {"name": "English", "flag": "🇬🇧"},
    "es": {"name": "Spanish", "flag": "🇪🇸"},
    "fr": {"name": "French", "flag": "🇫🇷"},
    "de": {"name": "German", "flag": "🇩🇪"},
    "it": {"name": "Italian", "flag": "🇮🇹"},
    "pt": {"name": "Portuguese", "flag": "🇵🇹"},
    "ru": {"name": "Russian", "flag": "🇷🇺"},
    "zh-cn": {"name": "Chinese (Simplified)", "flag": "🇨🇳"},
    "ja": {"name": "Japanese", "flag": "🇯🇵"},
    "ko": {"name": "Korean", "flag": "🇰🇷"},
    "ar": {"name": "Arabic", "flag": "🇸🇦"},
    "hi": {"name": "Hindi", "flag": "🇮🇳"},
    "tr": {"name": "Turkish", "flag": "🇹🇷"},
    "nl": {"name": "Dutch", "flag": "🇳🇱"},
    "pl": {"name": "Polish", "flag": "🇵🇱"},
    "uk": {"name": "Ukrainian", "flag": "🇺🇦"},
    "vi": {"name": "Vietnamese", "flag": "🇻🇳"},
    "th": {"name": "Thai", "flag": "🇹🇭"},
    "id": {"name": "Indonesian", "flag": "🇮🇩"},
    "ms": {"name": "Malay", "flag": "🇲🇾"},
    "fa": {"name": "Persian", "flag": "🇮🇷"},
    "he": {"name": "Hebrew", "flag": "🇮🇱"},
    "sv": {"name": "Swedish", "flag": "🇸🇪"},
    "no": {"name": "Norwegian", "flag": "🇳🇴"},
    "da": {"name": "Danish", "flag": "🇩🇰"},
    "fi": {"name": "Finnish", "flag": "🇫🇮"},
    "el": {"name": "Greek", "flag": "🇬🇷"},
    "bn": {"name": "Bengali", "flag": "🇧🇩"},
    "ta": {"name": "Tamil", "flag": "🇮🇳"},
    "te": {"name": "Telugu", "flag": "🇮🇳"},
    "ml": {"name": "Malayalam", "flag": "🇮🇳"},
    "ur": {"name": "Urdu", "flag": "🇵🇰"},
    "pa": {"name": "Punjabi", "flag": "🇮🇳"},
    "gu": {"name": "Gujarati", "flag": "🇮🇳"},
    "kn": {"name": "Kannada", "flag": "🇮🇳"},
    "or": {"name": "Odia", "flag": "🇮🇳"},
    "mr": {"name": "Marathi", "flag": "🇮🇳"},
    "ne": {"name": "Nepali", "flag": "🇳🇵"},
    "si": {"name": "Sinhala", "flag": "🇱🇰"},
    "my": {"name": "Burmese", "flag": "🇲🇲"},
    "km": {"name": "Khmer", "flag": "🇰🇭"},
    "lo": {"name": "Lao", "flag": "🇱🇦"},
}

# ==================== TRANSLATOR ====================

# Initialize translator
try:
    translator = Translator()
    logger.info("✅ Google Translate initialized successfully!")
except Exception as e:
    logger.error(f"❌ Failed to initialize translator: {e}")
    translator = None

def translate_text(text: str, dest_lang: str, src_lang: str = None) -> Dict:
    """
    Translate text using Google Translate API
    Returns: Dict with translation details
    """
    if not translator:
        return {
            "error": "Translation service unavailable. Please try again later."
        }
    
    try:
        # Perform translation
        if src_lang:
            result = translator.translate(text, dest=dest_lang, src=src_lang)
        else:
            result = translator.translate(text, dest=dest_lang)
        
        # Get detected source language
        detected_lang = result.src if result.src else src_lang
        
        # Get language names
        src_name = LANG_CODES.get(detected_lang, {}).get("name", detected_lang)
        dest_name = LANG_CODES.get(dest_lang, {}).get("name", dest_lang)
        
        return {
            "original": text,
            "translated": result.text,
            "source_lang": detected_lang,
            "target_lang": dest_lang,
            "source_name": src_name,
            "target_name": dest_name,
            "pronunciation": result.pronunciation if hasattr(result, 'pronunciation') else None,
            "auto_detected": not bool(src_lang)
        }
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return {
            "error": f"Translation failed: {str(e)}"
        }

def detect_language(text: str) -> str:
    """Detect language of text"""
    if not translator:
        return "en"
    
    try:
        result = translator.detect(text)
        return result.lang if result else "en"
    except:
        return "en"

# ==================== USER DATA ====================

user_data: Dict[int, Dict] = {}

def get_user_data(user_id: int) -> Dict:
    """Get or create user data"""
    if user_id not in user_data:
        user_data[user_id] = {
            "source_lang": None,  # None = auto-detect
            "target_lang": "es",
            "total_translations": 0,
            "favorite_langs": defaultdict(int),
            "last_text": "",
            "last_translation": ""
        }
    return user_data[user_id]

# ==================== KEYBOARDS ====================

def get_main_keyboard():
    """Create main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("🌐 Translate", callback_data="translate")],
        [InlineKeyboardButton("🔄 Swap Languages", callback_data="swap")],
        [InlineKeyboardButton("📋 Languages", callback_data="languages")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("📊 My Stats", callback_data="stats")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_language_keyboard(page: int = 0, selected: str = None, mode: str = "target"):
    """Create language selection keyboard"""
    keyboard = []
    lang_items = list(LANG_CODES.items())
    per_page = 8
    start = page * per_page
    end = min(start + per_page, len(lang_items))
    
    for i in range(start, end, 2):
        row = []
        for j in range(2):
            if i + j < end:
                code, lang = lang_items[i + j]
                is_selected = (code == selected)
                text = f"{'✅ ' if is_selected else ''}{lang['flag']} {lang['name']}"
                row.append(InlineKeyboardButton(
                    text,
                    callback_data=f"lang_{mode}_{code}"
                ))
        keyboard.append(row)
    
    # Navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"langpage_{mode}_{page-1}"))
    if end < len(lang_items):
        nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"langpage_{mode}_{page+1}"))
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard(user_id: int):
    """Create settings keyboard"""
    data = get_user_data(user_id)
    source = data.get("source_lang", "auto")
    target = data.get("target_lang", "es")
    
    source_name = LANG_CODES.get(source, {}).get("name", "Auto Detect") if source else "Auto Detect"
    target_name = LANG_CODES.get(target, {}).get("name", "Spanish")
    
    keyboard = [
        [InlineKeyboardButton(
            f"🔍 Source: {'Auto' if not source else source_name}",
            callback_data="set_source"
        )],
        [InlineKeyboardButton(
            f"🎯 Target: {target_name}",
            callback_data="set_target"
        )],
        [InlineKeyboardButton(
            "🔄 Swap Languages",
            callback_data="swap"
        )],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== COMMAND HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_id = str(user.id)
    data = get_user_data(user_id)
    
    welcome = (
        f"🌐 **Welcome to {BOT_NAME}!**\n\n"
        f"👋 Hello @{user.username or user.first_name}!\n\n"
        f"Your professional language translation assistant.\n\n"
        f"✨ **Features:**\n"
        f"• 🌐 Translate between 35+ languages\n"
        f"• 🔍 Auto-detect source language\n"
        f"• 🔄 Quick language swap\n"
        f"• 📋 Language list\n"
        f"• 📊 Usage statistics\n\n"
        f"📊 **Your Stats:**\n"
        f"• Total translations: {data['total_translations']}\n\n"
        f"⬇️ Send me any text or use the buttons below!"
    )
    
    await update.message.reply_text(
        welcome,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        f"📖 **{BOT_NAME} User Guide**\n\n"
        "**🌐 How to Translate:**\n"
        "• Send any text message\n"
        "• I'll auto-detect the language\n"
        "• Get translation instantly\n\n"
        "**⚙️ Settings:**\n"
        "• Change target language\n"
        "• Set source language (or auto-detect)\n"
        "• Swap languages\n\n"
        "**📌 Commands:**\n"
        "/start - Main menu\n"
        "/help - This help\n"
        "/stats - Your statistics\n"
        "/languages - List all languages"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    
    fav_langs = data.get("favorite_langs", defaultdict(int))
    top_langs = sorted(fav_langs.items(), key=lambda x: x[1], reverse=True)[:5]
    
    stats_text = (
        f"📊 **Your Statistics**\n\n"
        f"🌐 Total translations: {data['total_translations']}\n"
        f"🔤 Source: {'Auto' if not data.get('source_lang') else LANG_CODES.get(data['source_lang'], {}).get('name', 'Auto')}\n"
        f"🎯 Target: {LANG_CODES.get(data['target_lang'], {}).get('name', 'Spanish')}\n"
        f"📅 Account active since: {datetime.now().strftime('%Y-%m-%d')}\n\n"
    )
    
    if top_langs:
        stats_text += "🏆 **Top Languages:**\n"
        for lang_code, count in top_langs:
            lang_name = LANG_CODES.get(lang_code, {}).get("name", lang_code)
            flag = LANG_CODES.get(lang_code, {}).get("flag", "🌐")
            stats_text += f"• {flag} {lang_name}: {count}\n"
    
    await update.message.reply_text(
        stats_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def languages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /languages command"""
    lang_list = "🌐 **Supported Languages**\n\n"
    for code, lang in sorted(LANG_CODES.items(), key=lambda x: x[1]['name']):
        lang_list += f"{lang['flag']} **{lang['name']}** `{code}`\n"
    
    await update.message.reply_text(
        lang_list,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ==================== CALLBACK HANDLERS ====================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    action = query.data
    
    # ===== MAIN ACTIONS =====
    
    if action == "translate":
        await query.edit_message_text(
            "🌐 **Send me text to translate!**\n\n"
            "I'll auto-detect the language and translate it.\n\n"
            "⚙️ Use Settings to change target language.\n\n"
            "Just send any text message!",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        context.user_data["action"] = "translate_waiting"
        
    elif action == "swap":
        # Swap source and target
        source = data.get("source_lang")
        target = data.get("target_lang", "es")
        data["source_lang"] = target
        data["target_lang"] = source if source else "en"
        
        source_name = LANG_CODES.get(data["source_lang"], {}).get("name", "Auto Detect") if data["source_lang"] else "Auto Detect"
        target_name = LANG_CODES.get(data["target_lang"], {}).get("name", "English")
        
        await query.edit_message_text(
            f"🔄 **Languages Swapped!**\n\n"
            f"Source: {source_name}\n"
            f"Target: {target_name}\n\n"
            f"Send me text to translate!",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        context.user_data["action"] = "translate_waiting"
        
    elif action == "languages":
        await query.edit_message_text(
            "📋 **Select Target Language**\n\n"
            "Choose your target language:",
            parse_mode="Markdown",
            reply_markup=get_language_keyboard(0, data.get("target_lang", "es"), "target")
        )
        
    elif action == "settings":
        await query.edit_message_text(
            "⚙️ **Settings**\n\n"
            "Customize your translation experience:",
            parse_mode="Markdown",
            reply_markup=get_settings_keyboard(user_id)
        )
        
    elif action == "stats":
        fav_langs = data.get("favorite_langs", defaultdict(int))
        top_langs = sorted(fav_langs.items(), key=lambda x: x[1], reverse=True)[:5]
        
        stats_text = (
            f"📊 **Your Statistics**\n\n"
            f"🌐 Total translations: {data['total_translations']}\n"
            f"🔤 Source: {'Auto' if not data.get('source_lang') else LANG_CODES.get(data['source_lang'], {}).get('name', 'Auto')}\n"
            f"🎯 Target: {LANG_CODES.get(data['target_lang'], {}).get('name', 'Spanish')}\n"
            f"📅 Account active since: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        )
        
        if top_langs:
            stats_text += "🏆 **Top Languages:**\n"
            for lang_code, count in top_langs:
                lang_name = LANG_CODES.get(lang_code, {}).get("name", lang_code)
                flag = LANG_CODES.get(lang_code, {}).get("flag", "🌐")
                stats_text += f"• {flag} {lang_name}: {count}\n"
        
        await query.edit_message_text(
            stats_text,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        
    elif action == "help":
        help_text = (
            f"📖 **{BOT_NAME} User Guide**\n\n"
            "**🌐 How to Translate:**\n"
            "• Send any text message\n"
            "• I'll auto-detect the language\n"
            "• Get translation instantly\n\n"
            "**⚙️ Settings:**\n"
            "• Change target language\n"
            "• Set source language (or auto-detect)\n"
            "• Swap languages\n\n"
            "**📌 Commands:**\n"
            "/start - Main menu\n"
            "/help - This help\n"
            "/stats - Your statistics"
        )
        await query.edit_message_text(
            help_text,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        
    elif action == "back":
        await query.edit_message_text(
            "🏠 **Main Menu**\n\n"
            "What would you like to do?",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        context.user_data["action"] = None
        
    # ===== SETTINGS =====
    
    elif action == "set_source":
        await query.edit_message_text(
            "📋 **Select Source Language**\n\n"
            "Choose the source language (or select 'Auto' for auto-detection):",
            parse_mode="Markdown",
            reply_markup=get_language_keyboard(0, data.get("source_lang", None), "source")
        )
        
    elif action == "set_target":
        await query.edit_message_text(
            "📋 **Select Target Language**\n\n"
            "Choose the target language:",
            parse_mode="Markdown",
            reply_markup=get_language_keyboard(0, data.get("target_lang", "es"), "target")
        )
        
    # ===== LANGUAGE SELECTION =====
    
    elif action.startswith("lang_source_"):
        lang_code = action.replace("lang_source_", "")
        if lang_code in LANG_CODES:
            data["source_lang"] = lang_code
            lang_name = LANG_CODES[lang_code]["name"]
            await query.edit_message_text(
                f"✅ **Source Language Set!**\n\n"
                f"Source: {LANG_CODES[lang_code]['flag']} {lang_name}\n\n"
                f"Send me text to translate!",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            context.user_data["action"] = "translate_waiting"
            
    elif action.startswith("lang_target_"):
        lang_code = action.replace("lang_target_", "")
        if lang_code in LANG_CODES:
            data["target_lang"] = lang_code
            lang_name = LANG_CODES[lang_code]["name"]
            await query.edit_message_text(
                f"✅ **Target Language Set!**\n\n"
                f"Target: {LANG_CODES[lang_code]['flag']} {lang_name}\n\n"
                f"Send me text to translate!",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            context.user_data["action"] = "translate_waiting"
            
    # ===== LANGUAGE PAGE NAVIGATION =====
    
    elif action.startswith("langpage_"):
        parts = action.split("_")
        if len(parts) == 3:
            mode = parts[1]
            page = int(parts[2])
            await query.edit_message_text(
                "📋 **Select Language**\n\n"
                f"Choose your language:",
                parse_mode="Markdown",
                reply_markup=get_language_keyboard(page, data.get("target_lang", "es"), mode)
            )

# ==================== MESSAGE HANDLERS ====================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for translation"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    text = update.message.text.strip()
    
    if not text:
        await update.message.reply_text(
            "❌ Please send some text to translate!",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Get settings
    src_lang = data.get("source_lang")  # None = auto-detect
    dest_lang = data.get("target_lang", "es")
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "🌐 **Translating...**\n\n"
        "Please wait...",
        parse_mode="Markdown"
    )
    
    # Translate
    result = translate_text(text, dest_lang, src_lang)
    
    await processing_msg.delete()
    
    if "error" in result:
        await update.message.reply_text(
            f"❌ **Translation Failed**\n\n{result['error']}",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Update stats
    data["total_translations"] += 1
    data["favorite_langs"][result["target_lang"]] += 1
    data["last_text"] = text
    data["last_translation"] = result["translated"]
    
    # Format response
    source_name = LANG_CODES.get(result["source_lang"], {}).get("name", result["source_lang"])
    target_name = LANG_CODES.get(result["target_lang"], {}).get("name", result["target_lang"])
    
    response = (
        f"🌐 **Translation**\n\n"
        f"🔤 **From:** {source_name}\n"
        f"🔤 **To:** {target_name}\n"
        f"{'🔍 Auto-detected' if result.get('auto_detected', True) else ''}\n\n"
        f"📝 **Original:**\n{result['original']}\n\n"
        f"🔄 **Translated:**\n{result['translated']}\n\n"
    )
    
    if result.get('pronunciation'):
        response += f"🔊 **Pronunciation:** {result['pronunciation']}\n\n"
    
    response += f"💡 Send another text to translate!"
    
    await update.message.reply_text(
        response,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Swap Languages", callback_data="swap")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
        ])
    )
    
    context.user_data["action"] = "translate_waiting"

# ==================== MAIN ====================

async def post_init(application):
    """Post initialization"""
    logger.info("=" * 60)
    logger.info(f"🌐 {BOT_NAME} Started Successfully!")
    logger.info(f"🤖 Username: @{BOT_USERNAME}")
    logger.info(f"📦 Version: {BOT_VERSION}")
    logger.info(f"🌍 Supported Languages: {len(LANG_CODES)}")
    logger.info(f"✅ Real Translation: {'Enabled' if REAL_TRANSLATION else 'Disabled'}")
    logger.info("=" * 60)
    logger.info("✅ Bot is ready to translate!")
    logger.info("=" * 60)

def main():
    """Main entry point"""
    logger.info(f"🚀 Starting {BOT_NAME}...")
    logger.info(f"📡 Using token: {BOT_TOKEN[:15]}...{BOT_TOKEN[-5:]}")
    
    if not REAL_TRANSLATION:
        logger.warning("⚠️ googletrans not installed! Install with: pip install googletrans==4.0.0-rc1")
    
    application = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .post_init(post_init) \
        .build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("languages", languages_command))
    
    # Callback handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("✅ Bot is polling for updates...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
