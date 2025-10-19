# Telegram Deepseek Bot (Render-ready)

## Features
- File hosting via Telegram documents (30–40 MB). Users can download from DATA.
- Bottom navigation: Home | Deepseek | Setting.
- Top bar: DATA and AI Links (ChatGPT, Gemini, Meta AI, Grok).
- Deepseek chat inside Telegram:
  - Normal | Coder modes.
  - Image message support (caption becomes prompt).
  - Post-chat popup with "Don't show again" | "Feedback".
- Settings:
  - Font size: Small, Normal, Big, Code (monospace).
  - Feedback: send message to your TG group.

## Environment variables (Render)
- BOT_TOKEN
- ADMIN_IDS (e.g., `123456789,987654321`)
- GROUP_CHAT_ID (numeric)
- DEEPSEEK_API_KEY
- DEEPSEEK_API_URL (optional; default provided)
- WEBHOOK_MODE=false (we use long polling)
- PORT=10000

## Deploy to Render
1. Create a new "Web Service" on Render pointing to this repository.
2. Build command: `pip install -r requirements.txt`
3. Start command: `python main.py`
4. Set the environment variables above.
5. Ensure only one instance (Render free tier is fine). We use long polling.

## Admin usage
- Upload a file: Send a document to the bot from an admin account. It will store its `file_id`, name, and a placeholder description.
- Update description:
  - `/setdesc <index> <description>`
  - Index is zero-based in the DATA list.

## Notes
- File downloads: Telegram hosts the documents once uploaded; users download directly inside Telegram.
- Deepseek image support in this sample passes the `file_id` reference; for fully featured image-to-model, adjust `deepseek_client.py` to upload image bytes if your API supports it.
- Font "code" uses monospace via HTML/Markdown formatting.
