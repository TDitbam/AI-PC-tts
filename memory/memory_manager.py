from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Manages short-term (conversation history) and potentially long-term memory.
    """
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_history:
            self.history.pop(0)
        logger.debug(f"Added {role} message to history. Current length: {len(self.history)}")

    def get_history(self) -> List[Dict[str, str]]:
        """Retrieve the conversation history."""
        return self.history

    def clear_history(self):
        """Clear the conversation history."""
        self.history = []
        logger.info("Conversation history cleared.")

    def get_system_prompt(self) -> str:
        """Returns the system prompt defining the AI's persona."""
        return "You are Jarvis, a highly capable AI assistant. You are concise, helpful, and professional. You respond in the language of the user."
