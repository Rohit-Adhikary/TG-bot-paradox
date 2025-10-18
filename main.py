import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import requests
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store user data
user_data = {}

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
            system_msg = f"You are a {language} programming expert." if language else "You are a helpful AI assistant."
            
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
                return "⚠️ Service temporarily unavailable. Please try again."
                
        except Exception as e:
            return "❌ Error connecting to AI service. Please try again later."

# Initialize API
deepseek = DeepSeekAPI()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"language": None}
    
    keyboard = [
        [InlineKeyboardButton("💻 Coding Mode", callback_data="coding")],
        [InlineKeyboardButton("💬 General Chat", callback_data="general")]
    ]
    
    await update.message.reply_text(
        "🤖 **DeepSeek Coding Assistant**\n\nChoose your mode:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {"language": None}
    
    if query.data == "coding":
        # Language selection
        languages = ["Python", "JavaScript", "Java", "C++", "HTML/CSS", "SQL"]
        keyboard = []
        for lang in languages:
            keyboard.append([InlineKeyboardButton(lang, callback_data=f"lang_{lang}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
        
        await query.edit_message_text(
            "🖥️ **Select Programming Language:**",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "general":
        user_data[user_id]["language"] = None
        await query.edit_message_text(
            "💬 **General Chat Mode**\n\nYou can now ask me anything!"
        )
    
    elif query.data == "back":
        await start(update, context)
    
    elif query.data.startswith("lang_"):
        language = query.data[5:]
        user_data[user_id]["language"] = language
        await query.edit_message_text(
            f"✅ **{language} Mode Activated**\n\nYou can now send your code or programming questions!"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data:
        user_data[user_id] = {"language": None}
    
    user_msg = update.message.text
    
    # Show typing indicator
    await update.message.chat.send_action(action="typing")
    
    # Get user language
    language = user_data[user_id]["language"]
    
    # Get AI response
    response = deepseek.get_response(user_msg, language)
    
    # Send response
    await update.message.reply_text(response)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data:
        user_data[user_id]["language"] = None
    await update.message.reply_text("🔄 Session cleared! Use /start to begin again.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 **DeepSeek Bot Help**

**Commands:**
/start - Start the bot
/clear - Clear session
/help - Show this help

**Features:**
- Code assistance in multiple languages
- General AI conversations
- Simple and fast responses

**How to use:**
1. Click /start
2. Choose coding or general mode
3. If coding, select your language
4. Start asking questions!
    """
    await update.message.reply_text(help_text)

def main():
    # Get bot token
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN not found!")
        return
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start bot
    print("✅ Bot started successfully!")
    application.run_polling()

if __name__ == '__main__':
    main()