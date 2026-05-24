import os
import time
import queue
import threading
import asyncio
import re
import traceback
from typing import Dict, Any, Optional

import edge_tts
from deep_translator import GoogleTranslator
from pygame import mixer
from gtts import gTTS

from .app_logger import get_logger
from .yt_chat import youtube_collector
from .twitch_chat import twitch_collector
from .tiktok_chat import tiktok_collector

logger = get_logger("Engine")

class ChatTTSEngine:
    def __init__(self):
        self.is_running = False
        self.msg_queue = queue.Queue(maxsize=100)
        self.audio_queue = queue.Queue(maxsize=100)
        self.seen_messages = set()
        self.max_seen_messages = 500
        self.threads = []
        
        self.msg_dir = "msg_queue"
        self.audio_dir = "temp_audio"
        self._ensure_directories()
        
        self.voice = "th-TH-PremwadeeNeural"
        self.delay_per_char = 0.03
        self.max_delay = 2.0
        self.auto_translate = False
        self.translator = GoogleTranslator(source='auto', target='th')
        
        self._init_mixer()

    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        for d in [self.msg_dir, self.audio_dir]:
            if not os.path.exists(d): 
                os.makedirs(d)

    def _init_mixer(self):
        """Initialize pygame mixer."""
        try:
            mixer.init()
        except Exception as e:
            logger.error(f"Failed to initialize pygame mixer: {e}")

    def _cleanup_temp_files(self):
        """Remove old files from transient directories."""
        logger.info("Cleaning up old files...")
        for d in [self.msg_dir, self.audio_dir]:
            if os.path.exists(d):
                for f in os.listdir(d):
                    try: 
                        os.remove(os.path.join(d, f))
                    except: 
                        pass

    def extract_video_id(self, url_or_id: str) -> str:
        """Extract YouTube video ID from URL or return raw ID."""
        patterns = [
            r"v=([a-zA-Z0-9_-]{11})", 
            r"youtu\.be/([a-zA-Z0-9_-]{11})", 
            r"live/([a-zA-Z0-9_-]{11})",
            r"video/([a-zA-Z0-9_-]{11})/livestreaming"
        ]
        for p in patterns:
            m = re.search(p, url_or_id)
            if m: return m.group(1)
        return url_or_id.strip()

    def _process_message(self, data: Any) -> Optional[str]:
        """Filter, translate and format the incoming message."""
        if isinstance(data, str):
            return data
            
        author = data.get("author", "Unknown")
        message = data.get("message", "")

        # Length Filter
        if len(message) > 200:
            logger.warning(f"Message too long from {author}, skipped.")
            return None

        # Duplicate Filter
        msg_id = f"{author}:{message}"
        if msg_id in self.seen_messages:
            return None
        
        self.seen_messages.add(msg_id)
        if len(self.seen_messages) > self.max_seen_messages:
            self.seen_messages.clear()
            
        # Translation
        if self.auto_translate:
            try:
                if not any('\u0e00' <= char <= '\u0e7f' for char in message):
                    translated = self.translator.translate(message)
                    logger.info(f"Translated: {message} -> {translated}")
                    message = translated
            except Exception as te:
                logger.error(f"Translation Error: {te}")
        
        return f"{author} พูดว่า {message}"

    async def _generate_audio(self, text: str, path: str):
        """Generate audio file using edge-tts or gTTS fallback."""
        try:
            await edge_tts.Communicate(text, self.voice).save(path)
        except Exception as e:
            logger.warning(f"edge-tts failed, using gTTS fallback: {e}")
            try:
                lang_code = self.voice.split('-')[0] if '-' in self.voice else 'th'
                tts = gTTS(text=text, lang=lang_code)
                tts.save(path)
            except Exception as ge:
                logger.error(f"gTTS fallback also failed: {ge}")
                raise ge

    async def generator_task(self):
        """Main generator loop: process messages and generate audio."""
        logger.info(f"Generator started: {self.voice}")
        while self.is_running:
            try:
                try:
                    data = self.msg_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                processed_text = self._process_message(data)
                if not processed_text:
                    continue

                path = os.path.join(self.audio_dir, f"{int(time.time()*1000)}.mp3")
                
                try:
                    await self._generate_audio(processed_text, path)
                    self.audio_queue.put((path, len(processed_text)), timeout=1.0)
                except queue.Full:
                    logger.warning("Audio queue full, dropping message.")
                    if os.path.exists(path): os.remove(path)
                except Exception:
                    continue

            except Exception as e:
                logger.error(f"Generator Error: {e}")
                await asyncio.sleep(1)

    def player_loop(self):
        """Main player loop: play generated audio files."""
        logger.info("Player started")
        while self.is_running:
            try:
                try:
                    path, char_count = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                if os.path.exists(path):
                    try:
                        logger.info(f"Playing: {path}")
                        mixer.music.load(path)
                        mixer.music.play()
                        while mixer.music.get_busy() and self.is_running:
                            time.sleep(0.1)
                        mixer.music.unload()
                        
                        time.sleep(min(char_count * self.delay_per_char, self.max_delay))
                    except Exception as e: 
                        logger.error(f"Play Error: {e}")
                    finally:
                        try:
                            if os.path.exists(path): os.remove(path)
                        except: pass
            except Exception as e: 
                logger.error(f"Player Loop Error: {e}")

    def start(self, config_dict: Dict[str, Any]):
        """Initialize and start all engine components and collectors."""
        if self.is_running: return
        self.is_running = True
        
        # Load Config
        self.voice = config_dict.get("voice", "th-TH-PremwadeeNeural")
        self.delay_per_char = float(config_dict.get("delay_per_char", 0.03))
        self.max_delay = float(config_dict.get("max_delay", 2.0))
        self.auto_translate = config_dict.get("auto_translate") == "True"
        
        def run_engine():
            try:
                self._cleanup_temp_files()
                
                # Core Threads
                self.threads = [
                    threading.Thread(target=lambda: asyncio.run(self.generator_task()), daemon=True),
                    threading.Thread(target=self.player_loop, daemon=True)
                ]

                # Collectors
                is_running_check = lambda: self.is_running
                
                if config_dict.get("yt_enabled") == "True" and config_dict.get("yt_id"):
                    vid = self.extract_video_id(config_dict.get("yt_id", ""))
                    self.threads.append(threading.Thread(
                        target=youtube_collector, 
                        args=(vid, self.msg_queue, is_running_check), 
                        daemon=True
                    ))
                    
                if config_dict.get("tw_enabled") == "True" and config_dict.get("tw_channel"):
                    channel = config_dict.get("tw_channel", "")
                    self.threads.append(threading.Thread(
                        target=twitch_collector, 
                        args=(channel, self.msg_queue, is_running_check), 
                        daemon=True
                    ))

                if config_dict.get("tk_enabled") == "True" and config_dict.get("tk_username"):
                    username = config_dict.get("tk_username", "")
                    self.threads.append(threading.Thread(
                        target=tiktok_collector, 
                        args=(username, self.msg_queue, is_running_check), 
                        daemon=True
                    ))

                for t in self.threads: t.start()
                logger.info(f"Engine started with {len(self.threads)-2} collectors")
            except Exception as e:
                logger.error(f"Failed to start engine: {e}\n{traceback.format_exc()}")
                self.is_running = False

        threading.Thread(target=run_engine, daemon=True).start()

    def stop(self):
        """Stop all engine components."""
        self.is_running = False
        self.threads = []
        logger.info("Engine stopped")
