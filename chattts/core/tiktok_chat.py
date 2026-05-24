import asyncio
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, DisconnectEvent
from .app_logger import get_logger

logger = get_logger("TikTok")

def tiktok_collector(username, msg_queue, is_running_func):
    logger.info(f"TikTok Collector started: {username}")
    
    # Clean username if URL was provided
    if "tiktok.com/@" in username:
        username = username.split("@")[-1].split("/")[0].split("?")[0]
    elif username.startswith("@"):
        username = username[1:]

    async def run_tiktok():
        client = TikTokLiveClient(unique_id=username)

        @client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            try:
                if not is_running_func():
                    return
                msg_queue.put({"author": event.user.nickname, "message": event.comment})
            except Exception as e:
                if "'str' object has no attribute 'get_type'" in str(e):
                    pass # Ignore this specific internal library error during parsing
                else:
                    logger.error(f"TikTok Comment Error: {e}")

        @client.on(DisconnectEvent)
        async def on_disconnect(event: DisconnectEvent):
            logger.warning("TikTok disconnected. Reconnecting...")

        retry_delay = 10
        while is_running_func():
            try:
                await client.start()
                retry_delay = 10 # Reset on success
            except Exception as e:
                if "'str' object has no attribute 'get_type'" in str(e):
                    logger.error(f"TikTok Error: {e} (This is a known library bug, retrying...)")
                else:
                    logger.error(f"TikTok Error: {e}")
                
                if not is_running_func(): break
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)

    asyncio.run(run_tiktok())
