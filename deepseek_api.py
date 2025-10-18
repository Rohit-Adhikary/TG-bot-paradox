import os
import aiohttp
import json
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class DeepSeekAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    async def get_response(self, user_message: str, system_message: str = None, conversation_history: List[Dict] = None) -> str:
        """Get response from DeepSeek API"""
        
        # Prepare messages
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Prepare request data
        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "stream": False,
            "max_tokens": 4000,
            "temperature": 0.7
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=data,
                    timeout=30
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content']
                    else:
                        error_text = await response.text()
                        logger.error(f"DeepSeek API error: {response.status} - {error_text}")
                        return "I apologize, but I'm having trouble connecting to the AI service. Please try again in a moment."
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            return "Network error occurred. Please check your connection and try again."
        except asyncio.TimeoutError:
            logger.error("DeepSeek API timeout")
            return "The request timed out. Please try again."
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return "An unexpected error occurred. Please try again."