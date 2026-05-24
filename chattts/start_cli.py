import sys
import os
import time
import configparser
import traceback

# Add core directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from core.tts_engine import ChatTTSEngine
from core.app_logger import get_logger

logger = get_logger("CLI")
CONFIG_FILE = "config.ini"

def main():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")
    
    conf = {
        "yt_enabled": config.get("settings", "yt_enabled", fallback="True"),
        "yt_id": config.get("settings", "YOUTUBE_VIDEO_ID", fallback=""),
        "tw_enabled": config.get("settings", "tw_enabled", fallback="False"),
        "tw_channel": config.get("settings", "tw_channel", fallback=""),
        "tk_enabled": config.get("settings", "tk_enabled", fallback="False"),
        "tk_username": config.get("settings", "tk_username", fallback=""),
        "voice": config.get("settings", "VOICE", fallback="th-TH-PremwadeeNeural"),
        "delay_per_char": config.get("settings", "delay_per_char", fallback="0.03"),
        "max_delay": config.get("settings", "max_delay", fallback="2.0"),
        "auto_translate": config.get("settings", "auto_translate", fallback="False")
    }
    
    if conf["yt_enabled"] == "True" and not conf["yt_id"]:
        conf["yt_id"] = input("Enter YouTube Video ID/URL: ")

    engine = ChatTTSEngine()
    logger.info("--- Multi-Platform Chat TTS System Starting (CLI) ---")
    
    try:
        engine.start(conf)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping system via KeyboardInterrupt...")
    except Exception as e:
        logger.critical(f"Unexpected fatal error: {e}\n{traceback.format_exc()}")
    finally:
        engine.stop()
        logger.info("System stopped.")

if __name__ == "__main__":
    while True:
        try:
            main()
            break # ถ้าจบปกติ (เช่น user stop) ให้หลุดลูป
        except Exception as e:
            logger.error(f"System crashed, auto-restarting in 5 seconds... Error: {e}")
            time.sleep(5)
