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
            setup_logging()
            orchestrator = JarvisOrchestrator()
            run_gui(orchestrator) 
        except Exception as e:
            print(f"Failed to load GUI: {e}")
    else:
        asyncio.run(main())
