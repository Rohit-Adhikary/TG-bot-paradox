import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from deepseek_api import DeepSeekAPI
import json

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize DeepSeek API
deepseek_api = DeepSeekAPI(api_key=os.getenv('DEEPSEEK_API_KEY'))

# Store user sessions
user_sessions = {}

class UserSession:
    def __init__(self):
        self.programming_language = None
        self.conversation_history = []
        self.is_waiting_for_code = False

# Programming languages list
PROGRAMMING_LANGUAGES = [
    "Python", "JavaScript", "Java", "C++", "C#", "PHP", "Ruby", "Go", "Rust",
    "Swift", "Kotlin", "TypeScript", "HTML/CSS", "SQL", "R", "MATLAB", "Shell",
    "Dart", "Scala", "Perl"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with main menu"""
    user_id = update.effective_user.id
    
    # Initialize user session if not exists
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession()
    
    keyboard = [
        [InlineKeyboardButton("🚀 Coding with DeepSeek", callback_data="coding_mode")],
        [InlineKeyboardButton("💬 General Chat", callback_data="general_chat")],
        [InlineKeyboardButton("🛠️ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """
🤖 **Welcome to DeepSeek Coding Bot!**

A powerful coding assistant integrated with DeepSeek AI.

**Features:**
• 🚀 Code in multiple programming languages
• 💬 General AI conversations
• 🔍 Code explanation and debugging
• 📚 Learning assistance

Choose an option below to get started!
    """
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession()
    
    if query.data == "coding_mode":
        await show_programming_languages(query)
    elif query.data == "general_chat":
        user_sessions[user_id].programming_language = None
        await query.edit_message_text(
            "💬 **General Chat Mode Activated**\n\nNow you can chat with DeepSeek about anything!",
            parse_mode='Markdown'
        )
    elif query.data == "help":
        await show_help(query)
    elif query.data == "back_to_main":
        await show_main_menu(query)
    elif query.data.startswith("lang_"):
        language = query.data[5:]  # Remove "lang_" prefix
        user_sessions[user_id].programming_language = language
        await query.edit_message_text(
            f"✅ **{language} Mode Activated**\n\n"
            f"Now DeepSeek will assist you with {language} programming.\n"
            f"You can:\n"
            f"• Write code\n"
            f"• Ask for explanations\n"
            f"• Debug issues\n"
            f"• Learn concepts\n\n"
            f"Start by sending your code or question!",
            parse_mode='Markdown'
        )
    elif query.data == "clear_context":
        user_sessions[user_id].conversation_history = []
        await query.edit_message_text("🧹 **Context Cleared!**\n\nConversation history has been reset.", parse_mode='Markdown')

async def show_programming_languages(query):
    """Show programming language selection"""
    keyboard = []
    
    # Create buttons in rows of 2
    for i in range(0, len(PROGRAMMING_LANGUAGES), 2):
        row = []
        if i < len(PROGRAMMING_LANGUAGES):
            row.append(InlineKeyboardButton(PROGRAMMING_LANGUAGES[i], callback_data=f"lang_{PROGRAMMING_LANGUAGES[i]}"))
        if i + 1 < len(PROGRAMMING_LANGUAGES):
            row.append(InlineKeyboardButton(PROGRAMMING_LANGUAGES[i+1], callback_data=f"lang_{PROGRAMMING_LANGUAGES[i+1]}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🖥️ **Select Programming Language**\n\n"
        "Choose your preferred programming language for coding assistance:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_main_menu(query):
    """Show main menu"""
    keyboard = [
        [InlineKeyboardButton("🚀 Coding with DeepSeek", callback_data="coding_mode")],
        [InlineKeyboardButton("💬 General Chat", callback_data="general_chat")],
        [InlineKeyboardButton("🛠️ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🤖 **DeepSeek Coding Bot**\n\nChoose an option:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_help(query):
    """Show help information"""
    help_text = """
🛠️ **Help Guide**

**Available Commands:**
/start - Start the bot and show main menu
/clear - Clear conversation history
/language - Show programming language selection
/mode - Switch between coding and general chat

**Coding Features:**
• Code completion and generation
• Debugging assistance
• Code explanation
• Best practices guidance
• Multiple programming language support

**Tips:**
• Be specific in your code requests
• Provide error messages for debugging
• Use the clear command to reset context
• Select appropriate programming language for better results

**Supported Languages:** Python, JavaScript, Java, C++, C#, PHP, Ruby, Go, Rust, Swift, Kotlin, TypeScript, HTML/CSS, SQL, R, MATLAB, Shell, Dart, Scala, Perl
    """
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

async def clear_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear conversation history"""
    user_id = update.effective_user.id
    if user_id in user_sessions:
        user_sessions[user_id].conversation_history = []
    
    await update.message.reply_text("🧹 **Context Cleared!**\n\nConversation history has been reset.", parse_mode='Markdown')

async def show_languages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show programming language selection via command"""
    user_id = update.effective_user.id
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession()
    
    keyboard = []
    for i in range(0, len(PROGRAMMING_LANGUAGES), 2):
        row = []
        if i < len(PROGRAMMING_LANGUAGES):
            row.append(InlineKeyboardButton(PROGRAMMING_LANGUAGES[i], callback_data=f"lang_{PROGRAMMING_LANGUAGES[i]}"))
        if i + 1 < len(PROGRAMMING_LANGUAGES):
            row.append(InlineKeyboardButton(PROGRAMMING_LANGUAGES[i+1], callback_data=f"lang_{PROGRAMMING_LANGUAGES[i+1]}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🖥️ **Select Programming Language**\n\nChoose your preferred programming language:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession()
    
    # Show typing action
    await update.message.chat.send_action(action="typing")
    
    try:
        # Get user session
        session = user_sessions[user_id]
        
        # Prepare context for DeepSeek
        if session.programming_language:
            system_message = f"You are an expert {session.programming_language} programmer. Provide helpful, accurate code and explanations. Format code properly and explain concepts clearly."
        else:
            system_message = "You are a helpful AI assistant. Provide accurate and helpful responses."
        
        # Get response from DeepSeek
        response = await deepseek_api.get_response(
            user_message=user_message,
            system_message=system_message,
            conversation_history=session.conversation_history
        )
        
        # Update conversation history
        session.conversation_history.append({"role": "user", "content": user_message})
        session.conversation_history.append({"role": "assistant", "content": response})
        
        # Keep only last 10 messages to manage token limit
        if len(session.conversation_history) > 10:
            session.conversation_history = session.conversation_history[-10:]
        
        # Send response with appropriate formatting
        if session.programming_language and any(keyword in response.lower() for keyword in ['```', 'def ', 'function ', 'class ', 'import ', 'public ']):
            # Format as code if it looks like code
            formatted_response = f"**💻 {session.programming_language} Response:**\n\n{response}"
        else:
            formatted_response = f"**🤖 DeepSeek:**\n\n{response}"
        
        # Split long messages (Telegram has 4096 character limit)
        if len(formatted_response) > 4000:
            parts = [formatted_response[i:i+4000] for i in range(0, len(formatted_response), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='Markdown')
        else:
            await update.message.reply_text(formatted_response, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("❌ Sorry, I encountered an error. Please try again.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update.effective_message:
        await update.effective_message.reply_text(
            "❌ An error occurred. Please try again later."
        )

def main():
    """Start the bot"""
    # Get bot token from environment variable
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    # Create Application
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear_context))
    application.add_handler(CommandHandler("language", show_languages))
    application.add_handler(CommandHandler("mode", show_languages))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # Start the bot
    port = int(os.environ.get('PORT', 8443))
    webhook_url = os.getenv('WEBHOOK_URL')
    
    if webhook_url:
        # Use webhook for production (Render)
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=webhook_url,
            webhook_url=f"{webhook_url}/webhook"
        )
    else:
        # Use polling for development
        application.run_polling()

if __name__ == '__main__':
    main()