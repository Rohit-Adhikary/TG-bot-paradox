import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")

# UI constants
NAV_HOME = "Home"
NAV_DEEPSEEK = "Deepseek"
NAV_SETTINGS = "Setting"
TOP_DATA = "DATA"
AI_LOGO_TEXT = "AI Links"

# File limits: Telegram allows sending documents up to 50MB for bots (practical target 30–40MB)
MAX_DOC_SIZE_MB = 50

DATA_DIR = os.getenv("DATA_DIR", "data")
FILES_JSON = os.path.join(DATA_DIR, "files.json")
USERS_JSON = os.path.join(DATA_DIR, "users.json")

# Render note: we use long polling; ensure only one instance
POLLING_INTERVAL = float(os.getenv("POLLING_INTERVAL", "0.5"))