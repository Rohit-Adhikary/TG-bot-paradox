import asyncio
from typing import List

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from config import (
    BOT_TOKEN, ADMIN_IDS, GROUP_CHAT_ID,
    NAV_HOME, NAV_DEEPSEEK, NAV_SETTINGS, TOP_DATA, AI_LOGO_TEXT,
    FILES_JSON, USERS_JSON, POLLING_INTERVAL, MAX_DOC_SIZE_MB
)
from storage import (
    add_file, list_files, get_user, set_user, read_json, write_json
)
from deepseek_client import DeepseekClient


# ---------- UI Helpers ----------

def bottom_nav():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(NAV_HOME, callback_data="nav_home"),
            InlineKeyboardButton(NAV_DEEPSEEK, callback_data="nav_deepseek"),
            InlineKeyboardButton(NAV_SETTINGS, callback_data="nav_settings"),
        ]
    ])

def top_bar():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(TOP_DATA, callback_data="top_data"),
        ],
        [
            InlineKeyboardButton(AI_LOGO_TEXT, callback_data="ai_links"),
        ]
    ])

def apply_font(text: str, font: str) -> str:
    if font == "small":
        return f"{text}"
    elif font == "normal":
        return text
    elif font == "big":
        return f"<b>{text}</b>"
    elif font == "code":
        return f"<code>{text}</code>"
    return text

# ---------- Screens ----------

async def show_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(USERS_JSON, user_id)
    text = "Welcome to your hub.\nHome | Deepseek | Setting"
    txt = apply_font(text, user["font"])
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            txt, reply_markup=bottom_nav(), parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            txt, reply_markup=bottom_nav(), parse_mode=ParseMode.HTML
        )

async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0, page_size: int = 6):
    items = list_files(FILES_JSON)
    user_id = update.effective_user.id
    user = get_user(USERS_JSON, user_id)
    total = len(items)
    start = page * page_size
    end = min(start + page_size, total)
    text = f"DATA: {total} files\nSelect a file to Download or see Details."
    txt = apply_font(text, user["font"])

    rows = []
    for idx, item in enumerate(items[start:end], start=start):
        title = item.get("title", f"File {idx+1}")
        rows.append([InlineKeyboardButton(f"{title}", callback_data=f"file_{idx}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"data_page_{page-1}"))
    if end < total:
        nav.append(InlineKeyboardButton("Next ▶", callback_data=f"data_page_{page+1}"))

    # Add top bar and bottom nav
    keyboard_rows = [[InlineKeyboardButton(TOP_DATA, callback_data="top_data")],
                     [InlineKeyboardButton("Back", callback_data="nav_home")]] + rows
    if nav:
        keyboard_rows.append(nav)
    keyboard_rows.append([InlineKeyboardButton(NAV_HOME, callback_data="nav_home"),
                          InlineKeyboardButton(NAV_DEEPSEEK, callback_data="nav_deepseek"),
                          InlineKeyboardButton(NAV_SETTINGS, callback_data="nav_settings")])
    kb = InlineKeyboardMarkup(keyboard_rows)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)

async def show_file_actions(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int):
    items = list_files(FILES_JSON)
    if index < 0 or index >= len(items):
        await update.callback_query.answer("Invalid file.")
        return
    item = items[index]
    title = item.get("title", f"File {index+1}")
    desc = item.get("description", "No details provided.")
    text = f"{title}\nChoose: Download or Details."
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Download", callback_data=f"download_{index}")],
        [InlineKeyboardButton("Details", callback_data=f"details_{index}")],
        [InlineKeyboardButton("Back", callback_data="top_data")],
        [InlineKeyboardButton(NAV_HOME, callback_data="nav_home"),
         InlineKeyboardButton(NAV_DEEPSEEK, callback_data="nav_deepseek"),
         InlineKeyboardButton(NAV_SETTINGS, callback_data="nav_settings")]
    ])
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text, reply_markup=kb)

async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int):
    items = list_files(FILES_JSON)
    if index < 0 or index >= len(items):
        await update.callback_query.answer("Invalid file.")
        return
    item = items[index]
    file_id = item.get("file_id")
    title = item.get("title", f"File {index+1}")
    await update.callback_query.answer("Sending file...")
    await context.bot.send_document(chat_id=update.effective_chat.id, document=file_id, caption=title)

async def details_file(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int):
    items = list_files(FILES_JSON)
    if index < 0 or index >= len(items):
        await update.callback_query.answer("Invalid file.")
        return
    item = items[index]
    title = item.get("title", f"File {index+1}")
    desc = item.get("description", "No details provided.")
    text = f"{title}\n\nDetails:\n{desc}"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Back", callback_data=f"file_{index}")],
        [InlineKeyboardButton(NAV_HOME, callback_data="nav_home"),
         InlineKeyboardButton(NAV_DEEPSEEK, callback_data="nav_deepseek"),
         InlineKeyboardButton(NAV_SETTINGS, callback_data="nav_settings")]
    ])
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text, reply_markup=kb)

async def show_ai_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Simple AI hub links; Telegram opens them externally
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("ChatGPT", url="https://chat.openai.com/")],
        [InlineKeyboardButton("Gemini", url="https://gemini.google.com/")],
        [InlineKeyboardButton("Meta AI", url="https://www.meta.ai/")],
        [InlineKeyboardButton("Grok", url="https://x.ai/")],
        [InlineKeyboardButton("Back", callback_data="nav_home")],
        [InlineKeyboardButton(NAV_HOME, callback_data="nav_home"),
         InlineKeyboardButton(NAV_DEEPSEEK, callback_data="nav_deepseek"),
         InlineKeyboardButton(NAV_SETTINGS, callback_data="nav_settings")]
    ])
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("AI Links:", reply_markup=kb)
    else:
        await update.message.reply_text("AI Links:", reply_markup=kb)

# ---------- Deepseek ----------

deepseek = DeepseekClient()

async def show_deepseek_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Normal", callback_data="ds_mode_normal"),
         InlineKeyboardButton("Coder", callback_data="ds_mode_coder")],
        [InlineKeyboardButton("Back", callback_data="nav_home")],
        [InlineKeyboardButton(NAV_HOME, callback_data="nav_home"),
         InlineKeyboardButton(NAV_DEEPSEEK, callback_data="nav_deepseek"),
         InlineKeyboardButton(NAV_SETTINGS, callback_data="nav_settings")]
    ])
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Deepseek mode:\nChoose Normal or Coder.", reply_markup=kb)
    else:
        await update.message.reply_text("Deepseek mode:\nChoose Normal or Coder.", reply_markup=kb)

async def handle_deepseek_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(USERS_JSON, user_id)
    mode = user.get("deepseek_mode", "normal")
    prompt = update.message.text
    await update.message.chat.send_action("typing")
    content = await deepseek.chat(messages=[{"role": "user", "content": prompt}], mode=mode)
    # Code-friendly response in coder mode (monospace)
    if mode == "coder":
        await update.message.reply_text(f"{content}", parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text(content)

    # After chat: popup (if enabled)
    if user.get("feedback_popup", True):
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Don’t show again", callback_data="popup_disable")],
            [InlineKeyboardButton("Feedback", callback_data="feedback_open")]
        ])
        await update.message.reply_text("How do you feel with this bot?", reply_markup=kb)

async def handle_deepseek_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(USERS_JSON, user_id)
    mode = user.get("deepseek_mode", "normal")

    photo = update.message.photo[-1]  # highest resolution
    file = await context.bot.get_file(photo.file_id)
    # For simplicity, send the URL as a hint; production: download file and send bytes to API if supported
    prompt = update.message.caption or "Describe this image."
    content = await deepseek.chat(messages=[
        {"role": "user", "content": f"User prompt: {prompt}\nImage file_id: {photo.file_id}"}
    ], mode=mode)
    await update.message.reply_text(content)

    if user.get("feedback_popup", True):
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Don’t show again", callback_data="popup_disable")],
            [InlineKeyboardButton("Feedback", callback_data="feedback_open")]
        ])
        await update.message.reply_text("How do you feel with this bot?", reply_markup=kb)

# ---------- Settings ----------

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(USERS_JSON, user_id)
    txt = f"Settings\nFont: {user['font']}\nFeedback popup: {'on' if user['feedback_popup'] else 'off'}"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Font: Small", callback_data="font_small"),
         InlineKeyboardButton("Normal", callback_data="font_normal"),
         InlineKeyboardButton("Big", callback_data="font_big"),
         InlineKeyboardButton("Code", callback_data="font_code")],
        [InlineKeyboardButton("Feedback", callback_data="feedback_open")],
        [InlineKeyboardButton("Back", callback_data="nav_home")],
        [InlineKeyboardButton(NAV_HOME, callback_data="nav_home"),
         InlineKeyboardButton(NAV_DEEPSEEK, callback_data="nav_deepseek"),
         InlineKeyboardButton(NAV_SETTINGS, callback_data="nav_settings")]
    ])
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(txt, reply_markup=kb)
    else:
        await update.message.reply_text(txt, reply_markup=kb)

async def feedback_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "Send your feedback message now. It will be forwarded to the group."
    )
    context.user_data["awaiting_feedback"] = True

async def handle_feedback_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_feedback"):
        text = update.message.text
        uname = update.effective_user.username or update.effective_user.full_name
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=f"Feedback from @{uname} (ID:{update.effective_user.id}):\n{text}"
        )
        await update.message.reply_text("Thanks! Feedback sent.")
        context.user_data["awaiting_feedback"] = False

# ---------- Admin: file upload ----------

async def handle_document_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    doc = update.message.document
    size_mb = (doc.file_size or 0) / (1024 * 1024)
    if size_mb > MAX_DOC_SIZE_MB:
        await update.message.reply_text(f"File too large ({size_mb:.1f} MB). Max {MAX_DOC_SIZE_MB} MB.")
        return

    title = doc.file_name
    # Optional: description can be provided by replying with /setdesc
    add_file(FILES_JSON, {
        "title": title,
        "description": "Description pending. Use /setdesc <index> <text> to update.",
        "file_id": doc.file_id
    })
    await update.message.reply_text(f"Uploaded and indexed: {title}\nUsers can find it in DATA.")

async def set_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /setdesc <index> <description>")
        return
    idx = int(args[0])
    items = list_files(FILES_JSON)
    if idx < 0 or idx >= len(items):
        await update.message.reply_text("Invalid index.")
        return
    desc = " ".join(args[1:])
    items[idx]["description"] = desc
    write_json(FILES_JSON, {"items": items})
    await update.message.reply_text(f"Updated description for file {idx}.")

# ---------- Callbacks ----------

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data

    if data == "nav_home":
        await show_home(update, context)
    elif data == "nav_deepseek":
        await show_deepseek_menu(update, context)
    elif data == "nav_settings":
        await show_settings(update, context)
    elif data == "top_data":
        await show_data(update, context, page=0)
    elif data.startswith("data_page_"):
        page = int(data.split("_")[-1])
        await show_data(update, context, page=page)
    elif data.startswith("file_"):
        idx = int(data.split("_")[-1])
        await show_file_actions(update, context, idx)
    elif data.startswith("download_"):
        idx = int(data.split("_")[-1])
        await download_file(update, context, idx)
    elif data.startswith("details_"):
        idx = int(data.split("_")[-1])
        await details_file(update, context, idx)
    elif data == "ai_links":
        await show_ai_links(update, context)
    elif data in ("ds_mode_normal", "ds_mode_coder"):
        mode = "normal" if data.endswith("normal") else "coder"
        set_user(USERS_JSON, update.effective_user.id, "deepseek_mode", mode)
        await update.callback_query.answer(f"Mode set: {mode}")
        await update.callback_query.edit_message_text(f"Deepseek mode is now {mode}. Send a message.", reply_markup=bottom_nav())
    elif data == "font_small":
        set_user(USERS_JSON, update.effective_user.id, "font", "small")
        await show_settings(update, context)
    elif data == "font_normal":
        set_user(USERS_JSON, update.effective_user.id, "font", "normal")
        await show_settings(update, context)
    elif data == "font_big":
        set_user(USERS_JSON, update.effective_user.id, "font", "big")
        await show_settings(update, context)
    elif data == "font_code":
        set_user(USERS_JSON, update.effective_user.id, "font", "code")
        await show_settings(update, context)
    elif data == "feedback_open":
        await feedback_open(update, context)
    elif data == "popup_disable":
        set_user(USERS_JSON, update.effective_user.id, "feedback_popup", False)
        await update.callback_query.answer("Popup disabled.")

# ---------- Commands ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_home(update, context)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n"
        "/start - Home\n"
        "/data - DATA\n"
        "/deepseek - Deepseek\n"
        "/settings - Settings\n"
        "Admin:\n"
        "Upload file by sending as document.\n"
        "/setdesc <index> <text> - set file description."
    )

async def data_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_data(update, context, page=0)

async def deepseek_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_deepseek_menu(update, context)

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_settings(update, context)

# ---------- Router ----------

def is_in_deepseek_mode(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    # If user has selected deepseek mode, any text/photo is treated as deepseek prompt
    user = get_user(USERS_JSON, user_id)
    # We’ll assume: after choosing mode, user messages go to deepseek until they press Home
    return user.get("deepseek_mode") in ("normal", "coder")

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.user_data.get("awaiting_feedback"):
        await handle_feedback_message(update, context)
        return
    # If user is on deepseek, route text to deepseek
    await handle_deepseek_text(update, context)

async def photo_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await handle_deepseek_photo(update, context)

# ---------- Main ----------

def build_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("data", data_cmd))
    app.add_handler(CommandHandler("deepseek", deepseek_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document_upload))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    app.add_handler(MessageHandler(filters.PHOTO, photo_router))
    return app

async def main():
    app = build_app()
    await app.initialize()
    await app.start()
    # Long-polling
    await app.run_polling(poll_interval=POLLING_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())