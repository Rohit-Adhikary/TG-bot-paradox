import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import requests
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store user sessions
user_sessions = {}

class UserSession:
    def __init__(self):
        self.language = None
        self.history = []

# Programming languages
LANGUAGES = ["Python", "JavaScript", "Java", "C++", "HTML/CSS", "SQL"]

class DeepSeekAPI:
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def get_response(self, message, language=None):
        try:
            system_msg = f"You are a {language} expert programmer." if language else "You are a helpful AI assistant."
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": message}
                ],
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            response = requests.post(self.url, headers=self.headers, json=data, timeout=30)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return "Sorry, API error. Please try again."
                
        except Exception as e:
            return "Sorry, service unavailable. Try again later."

deepseek = DeepSeekAPI()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = UserSession()
    
    keyboard = [
        [InlineKeyboardButton("💻 Coding Mode", callback_data="coding")],
        [InlineKeyboardButton("💬 General Chat", callback_data="general")],
        [InlineKeyboardButton("🛠️ Help", callback_data="help")]
    ]
    
    await update.message.reply_text(
        "🤖 **DeepSeek Bot**\nChoose mode:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession()
    
    if query.data == "coding":
        # Show language buttons
        keyboard = []
        for lang in LANGUAGES:
            keyboard.append([InlineKeyboardButton(lang, callback_data=f"lang_{lang}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
        
        await query.edit_message_text(
            "Select programming language:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "general":
        user_sessions[user_id].language = None
        await query.edit_message_text("💬 **General Chat Mode**\nAsk me anything!")
    
    elif query.data == "help":
        help_text = """
**Commands:**
/start - Start bot
/clear - Clear history
/language - Select language

**Tips:**
- Be specific with questions
- Use /clear to reset chat
        """
        await query.edit_message_text(help_text, parse_mode='Markdown')
    
    elif query.data == "back":
        await start(update, context)
    
    elif query.data.startswith("lang_"):
        language = query.data[5:]
        user_sessions[user_id].language = language
        await query.edit_message_text(f"✅ **{language} Mode**\nStart coding!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession()
    
    user_msg = update.message.text
    session = user_sessions[user_id]
    
    await update.message.chat.send_action(action="typing")
    
    # Get AI response
    response = deepseek.get_response(user_msg, session.language)
    
    # Send response
    if len(response) > 4000:
        parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for part in parts:
            await update.message.reply_text(part)
    else:
        await update.message.reply_text(response)

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_sessions:
        user_sessions[user_id].history = []
    await update.message.reply_text("✅ History cleared!")

async def show_languages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession()
    
    keyboard = []
    for lang in LANGUAGES:
        keyboard.append([InlineKeyboardButton(lang, callback_data=f"lang_{lang}")])
    
    await update.message.reply_text(
        "Select language:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def main():
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN not found!")
        return
    
    app = Application.builder().token(bot_token).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(CommandHandler("language", show_languages))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start bot
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()