import time
import socket
import random
from .app_logger import get_logger

logger = get_logger("Twitch")

def twitch_collector(channel, msg_queue, is_running_func):
    logger.info(f"Twitch Collector started: {channel}")
    
    # Extract channel name if URL was provided
    if "twitch.tv/" in channel:
        channel_name = channel.split("twitch.tv/")[-1].strip("/")
    else:
        channel_name = channel
        
    retry_delay = 5
    while is_running_func():
        sock = None
        try:
            sock = socket.socket()
            sock.settimeout(10)
            sock.connect(("irc.chat.twitch.tv", 6667))
            
            retry_delay = 5 # Reset on success
            nick = f"justinfan{random.randint(100000, 999999)}"
            sock.send(f"PASS oauth:anonymous\r\n".encode("utf-8"))
            sock.send(f"NICK {nick}\r\n".encode("utf-8"))
            sock.send(f"JOIN #{channel_name.lower()}\r\n".encode("utf-8"))
            
            logger.info(f"Connected to Twitch IRC: {channel_name}")
            
            buffer = ""
            while is_running_func():
                try:
                    data = sock.recv(2048).decode("utf-8", errors="ignore")
                    if not data: break
                    
                    buffer += data
                    while "\r\n" in buffer:
                        line, buffer = buffer.split("\r\n", 1)
                        if line.startswith("PING"):
                            sock.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
                        elif "PRIVMSG" in line:
                            # Format: :nick!nick@nick.tmi.twitch.tv PRIVMSG #channel :message
                            try:
                                parts = line.split(":", 2)
                                if len(parts) >= 3:
                                    author = parts[1].split("!")[0]
                                    message = parts[2]
                                    msg_queue.put({"author": author, "message": message})
                            except Exception as parse_e:
                                logger.error(f"Error parsing Twitch line: {parse_e}")
                except socket.timeout:
                    continue
                except Exception as loop_e:
                    if is_running_func():
                        logger.error(f"Twitch Loop Error: {loop_e}")
                    break
        except Exception as e:
            if is_running_func():
                logger.error(f"Twitch Connection Error: {e}")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)
        finally:
            if sock:
                try: sock.close()
                except: pass
