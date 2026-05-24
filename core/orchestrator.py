import os
import asyncio
from typing import Dict, Any, List, Optional
import logging
from core.event_bus import EventBus
from core.config_manager import ConfigManager
from ai.ollama_client import OllamaClient
from memory.memory_manager import MemoryManager
from commands.command_router import CommandRouter, get_time_handler, weather_handler
from audio.audio_manager import AudioManager
from stt.stt_manager import STTManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from tts.tts_manager import TTSManager

class JarvisOrchestrator:
    """
    Main orchestrator for Jarvis AI Assistant.
    """
    def __init__(self):
        self.config = ConfigManager()
        self.event_bus = EventBus()
        
        # Load settings from config
        ai_model = self.config.get("AI", "model")
        ai_url = self.config.get("AI", "base_url")
        self.ai_client = OllamaClient(model=ai_model, base_url=ai_url)
        
        self.memory = MemoryManager()
        self.router = CommandRouter()
        
        device_id = int(self.config.get("AUDIO", "device_id", fallback="-1"))
        self.audio = AudioManager(device_id=None if device_id == -1 else device_id)
        
        stt_lang = self.config.get("STT", "language")
        self.stt = STTManager(language=stt_lang)
        self.stt.always_listen = self.config.get("STT", "always_listen") == "True"
        
        self.tts = TTSManager()
        # Sync TTS config
        self.tts.update_config({
            "voice": self.config.get("TTS", "voice"),
            "auto_translate": self.config.get("TTS", "auto_translate"),
            "delay_per_char": self.config.get("TTS", "delay_per_char")
        })
        
        self.is_running = False
        self._lock = asyncio.Lock() # To prevent concurrent start/stop

        self._setup_commands()
        self._setup_event_handlers()

    def _setup_commands(self):
        """Register default commands."""
        self.router.register_command("get_time", get_time_handler)
        self.router.register_command("get_weather", weather_handler)

    def _setup_event_handlers(self):
        """Subscribe to events."""
        self.event_bus.subscribe("user_speech", self._handle_user_speech)
        self.event_bus.subscribe("ai_response", self._handle_ai_response)

    async def start(self):
        """Start Jarvis."""
        async with self._lock:
            if self.is_running:
                logger.debug("Jarvis is already running.")
                return

            logger.info("Jarvis starting...")
            
            # Capture the current event loop for use in callbacks from other threads
            self.loop = asyncio.get_running_loop()
            
            try:
                self.audio.start_recording()
                
                def stt_callback(text):
                    if not self.is_running:
                        return
                        
                    # Use the captured loop to emit the event safely from the STT thread
                    self.loop.call_soon_threadsafe(
                        lambda: asyncio.create_task(self.event_bus.emit("user_speech", text))
                    )
                    
                self.stt.transcribe_stream(self.audio.input_queue, stt_callback)
                self.is_running = True
                await self.event_bus.emit("system_status", "Active")
                logger.info("Jarvis is ready and listening.")
            except Exception as e:
                logger.error(f"Failed to start Jarvis: {e}")
                self.is_running = False
                await self.event_bus.emit("system_status", "Error")

    async def stop(self):
        """Stop Jarvis."""
        async with self._lock:
            if not self.is_running:
                return

            logger.info("Jarvis stopping...")
            self.is_running = False
            self.audio.stop_recording()
            self.stt.stop()
            await self.event_bus.emit("system_status", "Stopped")
            logger.info("Jarvis stopped.")

    def change_audio_device(self, device_id: int):
        """Change the active audio input device."""
        logger.info(f"Changing audio device to {device_id}")
        was_running = self.is_recording if hasattr(self.audio, 'is_recording') else False
        
        self.audio.stop_recording()
        self.audio.device_id = device_id
        
        if self.is_running:
            self.audio.start_recording()

    async def _classify_intent(self, text: str) -> Optional[str]:
        """Use Ollama to classify user intent."""
        prompt = f"""
        Classify the following user input into one of these intents: get_time, get_weather, chat.
        Only respond with the intent name.
        
        User input: "{text}"
        Intent:"""
        
        try:
            intent = await self.ai_client.generate(prompt)
            intent = intent.strip().lower()
            
            if intent in ["get_time", "get_weather"]:
                return intent
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            
        return "chat"

    async def _handle_user_speech(self, text: str):
        """Handle transcribed user speech."""
        if not text or not text.strip():
            return

        logger.info(f"User said: {text}")
        self.memory.add_message("user", text)
        await self.event_bus.emit("system_status", "Thinking")
        
        try:
            intent = await self._classify_intent(text)
            logger.info(f"Classified intent: {intent}")
            
            if intent != "chat":
                response = await self.router.handle_intent(intent)
            else:
                # Stream response from Ollama
                full_response = ""
                messages = [{"role": "system", "content": self.memory.get_system_prompt()}]
                messages.extend(self.memory.get_history())
                
                async for chunk in self.ai_client.stream_chat(messages):
                    if not self.is_running:
                        break
                    full_response += chunk
                    await self.event_bus.emit("ai_response_chunk", chunk)
                
                response = full_response

            if self.is_running and response:
                self.memory.add_message("assistant", response)
                await self.event_bus.emit("ai_response", response)
                await self.event_bus.emit("system_status", "Active")
        except Exception as e:
            logger.error(f"Error handling speech: {e}")
            await self.event_bus.emit("system_status", "Active")

    async def _handle_ai_response(self, text: str):
        """Handle AI response."""
        logger.info(f"Jarvis: {text}")
        await self.tts.speak(text)

if __name__ == "__main__":
    async def main():
        jarvis = JarvisOrchestrator()
        await jarvis.start()
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await jarvis.stop()

    asyncio.run(main())
