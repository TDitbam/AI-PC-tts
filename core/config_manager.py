import configparser
import os
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages persistent configuration using a config.ini file.
    """
    def __init__(self, config_file: str = "config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self._load_defaults()
        self.load()

    def _load_defaults(self):
        """Set default values if the config file doesn't exist."""
        self.config["AI"] = {
            "model": "gemma4",
            "base_url": "http://localhost:11434"
        }
        self.config["STT"] = {
            "language": "th-TH",
            "always_listen": "True"
        }
        self.config["TTS"] = {
            "voice": "th-TH-PremwadeeNeural",
            "auto_translate": "False",
            "delay_per_char": "0.03"
        }
        self.config["AUDIO"] = {
            "device_id": "-1"  # -1 for default
        }

    def load(self):
        """Load configuration from the file."""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
            logger.info(f"Configuration loaded from {self.config_file}")
        else:
            self.save() # Create with defaults
            logger.info(f"Default configuration created at {self.config_file}")

    def save(self):
        """Save current configuration to the file."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            self.config.write(f)
        logger.info(f"Configuration saved to {self.config_file}")

    def get(self, section: str, key: str, fallback: str = None) -> str:
        return self.config.get(section, key, fallback=fallback)

    def set(self, section: str, key: str, value: str):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = str(value)
        self.save()
