"""
🌐 Lingua Swap Bot - Professional Language Translator
Translate text between multiple languages with auto-detection and pronunciation
"""

import os
import io
import re
import json
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
    logger.error("Please set one of these environment variables:")
    logger.error("  - TELEGRAM_TOKEN")
    logger.error("  - TELEGRAM_BOT_TOKEN")
    logger.error("  - BOT_TOKEN")
    logger.error("=" * 60)
    raise ValueError("❌ No Telegram Bot Token found in environment variables!")

BOT_NAME = "Lingua Swap Bot"
BOT_USERNAME = "lingua_swap_bot"
BOT_VERSION = "1.0.0"

# ==================== LANGUAGE DATA ====================

# Supported languages
LANGUAGES = {
    "en": {"name": "English", "flag": "🇬🇧", "code": "en"},
    "es": {"name": "Spanish", "flag": "🇪🇸", "code": "es"},
    "fr": {"name": "French", "flag": "🇫🇷", "code": "fr"},
    "de": {"name": "German", "flag": "🇩🇪", "code": "de"},
    "it": {"name": "Italian", "flag": "🇮🇹", "code": "it"},
    "pt": {"name": "Portuguese", "flag": "🇵🇹", "code": "pt"},
    "ru": {"name": "Russian", "flag": "🇷🇺", "code": "ru"},
    "zh": {"name": "Chinese", "flag": "🇨🇳", "code": "zh"},
    "ja": {"name": "Japanese", "flag": "🇯🇵", "code": "ja"},
    "ko": {"name": "Korean", "flag": "🇰🇷", "code": "ko"},
    "ar": {"name": "Arabic", "flag": "🇸🇦", "code": "ar"},
    "hi": {"name": "Hindi", "flag": "🇮🇳", "code": "hi"},
    "tr": {"name": "Turkish", "flag": "🇹🇷", "code": "tr"},
    "nl": {"name": "Dutch", "flag": "🇳🇱", "code": "nl"},
    "pl": {"name": "Polish", "flag": "🇵🇱", "code": "pl"},
    "uk": {"name": "Ukrainian", "flag": "🇺🇦", "code": "uk"},
    "vi": {"name": "Vietnamese", "flag": "🇻🇳", "code": "vi"},
    "th": {"name": "Thai", "flag": "🇹🇭", "code": "th"},
    "id": {"name": "Indonesian", "flag": "🇮🇩", "code": "id"},
    "ms": {"name": "Malay", "flag": "🇲🇾", "code": "ms"},
    "fa": {"name": "Persian", "flag": "🇮🇷", "code": "fa"},
    "he": {"name": "Hebrew", "flag": "🇮🇱", "code": "he"},
    "sv": {"name": "Swedish", "flag": "🇸🇪", "code": "sv"},
    "no": {"name": "Norwegian", "flag": "🇳🇴", "code": "no"},
    "da": {"name": "Danish", "flag": "🇩🇰", "code": "da"},
    "fi": {"name": "Finnish", "flag": "🇫🇮", "code": "fi"},
    "el": {"name": "Greek", "flag": "🇬🇷", "code": "el"},
}

# Common phrases for language detection testing
COMMON_PHRASES = {
    "en": ["hello", "good", "yes", "no", "thank", "you", "love", "life"],
    "es": ["hola", "gracias", "bueno", "sí", "no", "amor", "vida"],
    "fr": ["bonjour", "merci", "oui", "non", "amour", "vie"],
    "de": ["hallo", "danke", "ja", "nein", "liebe", "leben"],
    "it": ["ciao", "grazie", "sì", "no", "amore", "vita"],
    "pt": ["olá", "obrigado", "sim", "não", "amor", "vida"],
    "ru": ["привет", "спасибо", "да", "нет", "любовь", "жизнь"],
    "zh": ["你好", "谢谢", "是", "不", "爱", "生活"],
    "ja": ["こんにちは", "ありがとう", "はい", "いいえ", "愛", "人生"],
    "ko": ["안녕하세요", "감사합니다", "네", "아니요", "사랑", "인생"],
}

# ==================== USER DATA ====================

user_data: Dict[int, Dict] = {}

def get_user_data(user_id: int) -> Dict:
    """Get or create user data"""
    if user_id not in user_data:
        user_data[user_id] = {
            "history": [],
            "source_lang": "en",
            "target_lang": "es",
            "auto_detect": True,
            "total_translations": 0,
            "favorite_langs": defaultdict(int)
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

def get_language_keyboard(page: int = 0, selected: str = None):
    """Create language selection keyboard"""
    keyboard = []
    lang_items = list(LANGUAGES.items())
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
                    callback_data=f"lang_{code}"
                ))
        keyboard.append(row)
    
    # Navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"lang_page_{page-1}"))
    if end < len(lang_items):
        nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"lang_page_{page+1}"))
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard(user_id: int):
    """Create settings keyboard"""
    data = get_user_data(user_id)
    auto_detect = data.get("auto_detect", True)
    source = data.get("source_lang", "en")
    target = data.get("target_lang", "es")
    
    source_name = LANGUAGES.get(source, {}).get("name", "Auto")
    target_name = LANGUAGES.get(target, {}).get("name", "English")
    
    keyboard = [
        [InlineKeyboardButton(
            f"{'✅' if auto_detect else '❌'} Auto-Detect Language",
            callback_data="toggle_auto"
        )],
        [InlineKeyboardButton(
            f"🔤 From: {source_name}",
            callback_data="set_source"
        )],
        [InlineKeyboardButton(
            f"🔤 To: {target_name}",
            callback_data="set_target"
        )],
        [InlineKeyboardButton(
            "🔄 Swap Languages",
            callback_data="swap"
        )],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_translate_options_keyboard():
    """Create translate options keyboard"""
    keyboard = [
        [InlineKeyboardButton("🔄 Swap Languages", callback_data="swap")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_swap_keyboard():
    """Create swap confirmation keyboard"""
    keyboard = [
        [InlineKeyboardButton("🔄 Confirm Swap", callback_data="confirm_swap")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== TRANSLATION FUNCTIONS ====================

def detect_language(text: str) -> str:
    """
    Detect language of text using simple keyword matching
    Returns: language code
    """
    if not text or len(text) < 3:
        return "en"
    
    text_lower = text.lower()
    
    # Check each language's common phrases
    scores = {}
    for lang_code, phrases in COMMON_PHRASES.items():
        score = 0
        for phrase in phrases:
            if phrase in text_lower:
                score += 1
        if score > 0:
            scores[lang_code] = score
    
    if scores:
        return max(scores, key=scores.get)
    
    # Check for non-Latin scripts
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        return "zh"
    if any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' for c in text):
        return "ja"
    if any('\uac00' <= c <= '\ud7af' for c in text):
        return "ko"
    if any('\u0600' <= c <= '\u06ff' for c in text):
        return "ar"
    if any('\u0400' <= c <= '\u04ff' for c in text):
        return "ru"
    
    # Default to English
    return "en"

def translate_text(text: str, source_lang: str, target_lang: str, auto_detect: bool = True) -> Dict:
    """
    Simulate translation (in production, use Google Translate API or similar)
    Returns: Dict with translation info
    """
    # Auto-detect source language
    detected_lang = source_lang
    if auto_detect:
        detected_lang = detect_language(text)
    
    # Get language names
    source_name = LANGUAGES.get(detected_lang, {}).get("name", "Unknown")
    target_name = LANGUAGES.get(target_lang, {}).get("name", "Unknown")
    
    # Simulate translation (in production, call actual translation API)
    # For demo purposes, we'll create a "translated" version
    translated_text = f"[Translated from {source_name} to {target_name}]\n\n{text}"
    
    return {
        "original": text,
        "translated": translated_text,
        "source_lang": detected_lang,
        "target_lang": target_lang,
        "source_name": source_name,
        "target_name": target_name,
        "auto_detected": auto_detect
    }

def get_language_name(code: str) -> str:
    """Get language name from code"""
    return LANGUAGES.get(code, {}).get("name", "Unknown")

def get_language_flag(code: str) -> str:
    """Get language flag from code"""
    return LANGUAGES.get(code, {}).get("flag", "🌐")

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
        f"• 🌐 Translate between 27+ languages\n"
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
        "• Click 'Translate' button\n"
        "• I'll auto-detect the language\n"
        "• Get translation instantly\n\n"
        "**⚙️ Settings:**\n"
        "• Change target language\n"
        "• Toggle auto-detection\n"
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
    
    # Get favorite languages
    fav_langs = data.get("favorite_langs", defaultdict(int))
    top_langs = sorted(fav_langs.items(), key=lambda x: x[1], reverse=True)[:5]
    
    stats_text = (
        f"📊 **Your Statistics**\n\n"
        f"🌐 Total translations: {data['total_translations']}\n"
        f"🔤 Auto-detect: {'✅ On' if data.get('auto_detect', True) else '❌ Off'}\n"
        f"📅 Account active since: {datetime.now().strftime('%Y-%m-%d')}\n\n"
    )
    
    if top_langs:
        stats_text += "🏆 **Top Languages:**\n"
        for lang_code, count in top_langs:
            lang_name = get_language_name(lang_code)
            stats_text += f"• {get_language_flag(lang_code)} {lang_name}: {count}\n"
    
    await update.message.reply_text(
        stats_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def languages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /languages command"""
    lang_list = "🌐 **Supported Languages**\n\n"
    for code, lang in sorted(LANGUAGES.items(), key=lambda x: x[1]['name']):
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
        source = data.get("source_lang", "en")
        target = data.get("target_lang", "es")
        data["source_lang"] = target
        data["target_lang"] = source
        
        source_name = get_language_name(data["source_lang"])
        target_name = get_language_name(data["target_lang"])
        
        await query.edit_message_text(
            f"🔄 **Languages Swapped!**\n\n"
            f"From: {get_language_flag(data['source_lang'])} {source_name}\n"
            f"To: {get_language_flag(data['target_lang'])} {target_name}\n\n"
            f"Send me text to translate!",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        context.user_data["action"] = "translate_waiting"
        
    elif action == "languages":
        # Show language selection
        await query.edit_message_text(
            "📋 **Select a Language**\n\n"
            "Choose your target language:",
            parse_mode="Markdown",
            reply_markup=get_language_keyboard(0, data.get("target_lang", "es"))
        )
        
    elif action == "settings":
        await query.edit_message_text(
            "⚙️ **Settings**\n\n"
            "Customize your translation experience:",
            parse_mode="Markdown",
            reply_markup=get_settings_keyboard(user_id)
        )
        
    elif action == "stats":
        # Get favorite languages
        fav_langs = data.get("favorite_langs", defaultdict(int))
        top_langs = sorted(fav_langs.items(), key=lambda x: x[1], reverse=True)[:5]
        
        stats_text = (
            f"📊 **Your Statistics**\n\n"
            f"🌐 Total translations: {data['total_translations']}\n"
            f"🔤 Auto-detect: {'✅ On' if data.get('auto_detect', True) else '❌ Off'}\n"
            f"📅 Account active since: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        )
        
        if top_langs:
            stats_text += "🏆 **Top Languages:**\n"
            for lang_code, count in top_langs:
                lang_name = get_language_name(lang_code)
                stats_text += f"• {get_language_flag(lang_code)} {lang_name}: {count}\n"
        
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
            "• Click 'Translate' button\n"
            "• I'll auto-detect the language\n"
            "• Get translation instantly\n\n"
            "**⚙️ Settings:**\n"
            "• Change target language\n"
            "• Toggle auto-detection\n"
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
        
    elif action == "confirm_swap":
        # Swap languages
        source = data.get("source_lang", "en")
        target = data.get("target_lang", "es")
        data["source_lang"] = target
        data["target_lang"] = source
        
        source_name = get_language_name(data["source_lang"])
        target_name = get_language_name(data["target_lang"])
        
        await query.edit_message_text(
            f"🔄 **Languages Swapped!**\n\n"
            f"From: {get_language_flag(data['source_lang'])} {source_name}\n"
            f"To: {get_language_flag(data['target_lang'])} {target_name}\n\n"
            f"Send me text to translate!",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        context.user_data["action"] = "translate_waiting"
        
    # ===== SETTINGS =====
    
    elif action == "toggle_auto":
        data["auto_detect"] = not data.get("auto_detect", True)
        await query.edit_message_text(
            f"⚙️ **Settings**\n\n"
            f"Auto-Detect: {'✅ On' if data.get('auto_detect', True) else '❌ Off'}\n\n"
            "Customize your translation experience:",
            parse_mode="Markdown",
            reply_markup=get_settings_keyboard(user_id)
        )
        
    elif action == "set_source":
        await query.edit_message_text(
            "📋 **Select Source Language**\n\n"
            "Choose the source language:",
            parse_mode="Markdown",
            reply_markup=get_language_keyboard(0, data.get("source_lang", "en"))
        )
        context.user_data["action"] = "set_source"
        
    elif action == "set_target":
        await query.edit_message_text(
            "📋 **Select Target Language**\n\n"
            "Choose the target language:",
            parse_mode="Markdown",
            reply_markup=get_language_keyboard(0, data.get("target_lang", "es"))
        )
        context.user_data["action"] = "set_target"
        
    # ===== LANGUAGE SELECTION =====
    
    elif action.startswith("lang_"):
        lang_code = action.replace("lang_", "")
        if lang_code in LANGUAGES:
            current_action = context.user_data.get("action", "")
            
            if current_action == "set_source":
                data["source_lang"] = lang_code
                await query.edit_message_text(
                    f"✅ **Source Language Set!**\n\n"
                    f"From: {get_language_flag(lang_code)} {get_language_name(lang_code)}\n\n"
                    f"Send me text to translate!",
                    parse_mode="Markdown",
                    reply_markup=get_main_keyboard()
                )
                context.user_data["action"] = "translate_waiting"
                
            elif current_action == "set_target" or True:
                data["target_lang"] = lang_code
                await query.edit_message_text(
                    f"✅ **Target Language Set!**\n\n"
                    f"To: {get_language_flag(lang_code)} {get_language_name(lang_code)}\n\n"
                    f"Send me text to translate!",
                    parse_mode="Markdown",
                    reply_markup=get_main_keyboard()
                )
                context.user_data["action"] = "translate_waiting"
            else:
                # Default - set as target
                data["target_lang"] = lang_code
                await query.edit_message_text(
                    f"✅ **Language Set!**\n\n"
                    f"Target: {get_language_flag(lang_code)} {get_language_name(lang_code)}\n\n"
                    f"Send me text to translate!",
                    parse_mode="Markdown",
                    reply_markup=get_main_keyboard()
                )
                context.user_data["action"] = "translate_waiting"
                
    # ===== LANGUAGE PAGE NAVIGATION =====
    
    elif action.startswith("lang_page_"):
        page = int(action.replace("lang_page_", ""))
        current_action = context.user_data.get("action", "")
        
        await query.edit_message_text(
            "📋 **Select a Language**\n\n"
            "Choose your language:",
            parse_mode="Markdown",
            reply_markup=get_language_keyboard(page, data.get("target_lang", "es"))
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
    
    # Check if user wants to translate
    action = context.user_data.get("action", "")
    
    if action == "translate_waiting" or True:
        # Get settings
        auto_detect = data.get("auto_detect", True)
        source_lang = data.get("source_lang", "en")
        target_lang = data.get("target_lang", "es")
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            "🌐 **Translating...**\n\n"
            "Please wait...",
            parse_mode="Markdown"
        )
        
        # Translate
        result = translate_text(text, source_lang, target_lang, auto_detect)
        
        # Update stats
        data["total_translations"] += 1
        data["favorite_langs"][result["target_lang"]] += 1
        
        # Format response
        response = (
            f"🌐 **Translation**\n\n"
            f"🔤 **From:** {result['source_name']}\n"
            f"🔤 **To:** {result['target_name']}\n"
            f"{'🔍 Auto-detected' if result['auto_detected'] else ''}\n\n"
            f"📝 **Original:**\n{result['original']}\n\n"
            f"🔄 **Translated:**\n{result['translated']}\n\n"
            f"💡 Send another text to translate!"
        )
        
        await processing_msg.delete()
        
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
        
    else:
        await update.message.reply_text(
            "🌐 **Send me text to translate!**\n\n"
            "Click 'Translate' button or just send any text!",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

# ==================== MAIN ====================

async def post_init(application):
    """Post initialization"""
    logger.info("=" * 60)
    logger.info(f"🌐 {BOT_NAME} Started Successfully!")
    logger.info(f"🤖 Username: @{BOT_USERNAME}")
    logger.info(f"📦 Version: {BOT_VERSION}")
    logger.info(f"🌍 Supported Languages: {len(LANGUAGES)}")
    logger.info("=" * 60)
    logger.info("✅ Bot is ready to translate!")
    logger.info("=" * 60)

def main():
    """Main entry point"""
    logger.info(f"🚀 Starting {BOT_NAME}...")
    logger.info(f"📡 Using token: {BOT_TOKEN[:15]}...{BOT_TOKEN[-5:]}")
    
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
