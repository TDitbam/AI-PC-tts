from typing import Any, Callable, Dict, Optional, List
import logging
import asyncio

logger = logging.getLogger(__name__)

class CommandRouter:
    """
    Routes identified intents to their respective handler functions.
    """
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}

    def register_command(self, intent: str, handler: Callable):
        """Register a handler for a specific intent."""
        self._handlers[intent] = handler
        logger.debug(f"Registered handler for intent: {intent}")

    async def handle_intent(self, intent: str, entities: Optional[Dict[str, Any]] = None) -> Any:
        """Execute the handler for a given intent."""
        handler = self._handlers.get(intent)
        if not handler:
            logger.warning(f"No handler registered for intent: {intent}")
            return f"I don't know how to handle '{intent}'."

        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(entities or {})
            else:
                return handler(entities or {})
        except Exception as e:
            logger.exception(f"Error executing handler for {intent}")
            return f"Error: {str(e)}"

# Example commands
async def get_time_handler(entities):
    from datetime import datetime
    return f"The current time is {datetime.now().strftime('%H:%M')}."

async def weather_handler(entities):
    location = entities.get("location", "your location")
    return f"I'm sorry, I cannot check the weather for {location} yet."
