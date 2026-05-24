import logging
import asyncio
from typing import Optional, Dict, Any
from .tts_engine import ChatTTSEngine

logger = logging.getLogger(__name__)

class TTSManager:
    """
    Wrapper for the ChatTTSEngine.
    """
    def __init__(self, engine_type: str = "chat_tts"):
        self.engine_type = engine_type
        self.engine = ChatTTSEngine()
        
        # Default config for the engine
        self.config = {
            "voice": "th-TH-PremwadeeNeural",
            "delay_per_char": 0.03,
            "max_delay": 2.0,
            "auto_translate": "False"
        }
        
        self.engine.start(self.config)
        logger.info(f"TTS Manager initialized with ChatTTSEngine")

    async def speak(self, text: str):
        """
        Convert text to speech using the engine's queue.
        """
        logger.info(f"TTS Request: {text}")
        # ChatTTSEngine uses a queue and background threads
        self.engine.msg_queue.put(text)
        
    def stop(self):
        """Stop the engine."""
        self.engine.stop()
