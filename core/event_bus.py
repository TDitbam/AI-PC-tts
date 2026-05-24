import asyncio
from typing import Any, Callable, Dict, List, Set
import logging

logger = logging.getLogger(__name__)

class EventBus:
    """
    A simple asynchronous event bus for decoupled communication between modules.
    """
    def __init__(self):
        self._listeners: Dict[str, Set[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = set()
        self._listeners[event_type].add(callback)
        logger.debug(f"Subscribed {callback.__name__} to {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event type."""
        if event_type in self._listeners:
            self._listeners[event_type].discard(callback)
            logger.debug(f"Unsubscribed {callback.__name__} from {event_type}")

    async def emit(self, event_type: str, data: Any = None):
        """Emit an event to all subscribers."""
        if event_type not in self._listeners:
            return

        tasks = []
        for callback in self._listeners[event_type]:
            if asyncio.iscoroutinefunction(callback):
                tasks.append(callback(data))
            else:
                # Wrap synchronous callbacks in a thread to avoid blocking the loop
                # though ideally all callbacks should be async for this project.
                loop = asyncio.get_running_loop()
                tasks.append(loop.run_in_executor(None, callback, data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.debug(f"Emitted {event_type} with data: {data}")
