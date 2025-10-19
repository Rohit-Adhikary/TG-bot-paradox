import httpx
from typing import Optional, List, Dict
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL

class DeepseekClient:
    def __init__(self, api_key: str = DEEPSEEK_API_KEY, base_url: str = DEEPSEEK_API_URL):
        self.api_key = api_key
        self.base_url = base_url

    async def chat(self, messages: List[Dict], mode: str = "normal") -> str:
        """
        mode: normal | coder
        - normal: concise helpful replies
        - coder: maximize code completeness, return longer code blocks
        """
        system = "You are Deepseek. Be accurate and helpful."
        if mode == "coder":
            system = "You are Deepseek Coder. Provide complete, large, copy-ready code with explanations when needed."

        payload = {
            "model": "deepseek-chat",  # adjust if your account requires a specific model name
            "messages": [{"role": "system", "content": system}] + messages,
            "temperature": 0.2 if mode == "coder" else 0.7,
            "max_tokens": 2048 if mode == "normal" else 8192,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(self.base_url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            # Adjust parsing to Deepseek API response format if needed
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            return content or "No content returned."