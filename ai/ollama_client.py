import aiohttp
import json
import asyncio
from typing import AsyncGenerator, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    """
    Client for interacting with Ollama API.
    """
    def __init__(self, model: str = "qwen2:7b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.api_generate = f"{self.base_url}/api/generate"
        self.api_chat = f"{self.base_url}/api/chat"

    async def stream_chat(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        Stream chat responses from Ollama with retry logic.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.api_chat, json=payload, timeout=30) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Ollama error (Attempt {attempt+1}): {response.status} - {error_text}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
                                continue
                            yield f"Error: {response.status}. Please check if Ollama is running."
                            return

                        async for line in response.content:
                            if line:
                                try:
                                    chunk = json.loads(line)
                                    if "message" in chunk and "content" in chunk["message"]:
                                        yield chunk["message"]["content"]
                                    if chunk.get("done"):
                                        return
                                except json.JSONDecodeError:
                                    continue
                return # Success
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Connection attempt {attempt+1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    yield f"Connection Error: Could not connect to Ollama after {max_retries} attempts."

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
                async with session.post(self.api_generate, json=payload, timeout=10) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama error: {response.status} - {error_text}")
                        return f"Error: {response.status}"
                    
                    result = await response.json()
                    return result.get("response", "")
        except Exception as e:
            logger.exception("Failed to connect to Ollama")
            return f"Connection Error: {str(e)}"
