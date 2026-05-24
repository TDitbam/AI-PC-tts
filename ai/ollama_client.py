import aiohttp
import json
from typing import AsyncGenerator, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    """
    Client for interacting with Ollama API.
    """
    def __init__(self, model: str = "qwen3:8b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.api_generate = f"{self.base_url}/api/generate"
        self.api_chat = f"{self.base_url}/api/chat"

    async def stream_chat(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        Stream chat responses from Ollama.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_chat, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama error: {response.status} - {error_text}")
                        yield f"Error: {response.status}"
                        return

                    async for line in response.content:
                        if line:
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                yield chunk["message"]["content"]
                            if chunk.get("done"):
                                break
        except Exception as e:
            logger.exception("Failed to connect to Ollama")
            yield f"Connection Error: {str(e)}"

    async def generate(self, prompt: str) -> str:
        """
        Generate a complete response for a prompt.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_generate, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama error: {response.status} - {error_text}")
                        return f"Error: {response.status}"
                    
                    result = await response.json()
                    return result.get("response", "")
        except Exception as e:
            logger.exception("Failed to connect to Ollama")
            return f"Connection Error: {str(e)}"
