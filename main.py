import asyncio
import logging
import sys
from core.orchestrator import JarvisOrchestrator
from core.logging_config import setup_logging

async def main():
    setup_logging()
    logger = logging.getLogger("Jarvis")
    
    orchestrator = JarvisOrchestrator()
    await orchestrator.start()
    
    logger.info("Jarvis is running. Press Ctrl+C to stop.")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping Jarvis...")
        await orchestrator.stop()

if __name__ == "__main__":
    # Check if GUI is requested
    if "--gui" in sys.argv:
        try:
            from gui.main_window import run_gui
            # Running GUI requires its own event loop management
            # This is a simplified integration
            orchestrator = JarvisOrchestrator()
            # We need to start orchestrator in a background thread or properly integrate loops
            # For now, we'll just show how it would be called.
            logger = logging.getLogger("Jarvis")
            logger.warning("GUI integration is a prototype and may require 'qasync' for full async support.")
            # run_gui(orchestrator) 
        except ImportError as e:
            print(f"Failed to load GUI: {e}. Ensure PySide6 is installed.")
    else:
        asyncio.run(main())
