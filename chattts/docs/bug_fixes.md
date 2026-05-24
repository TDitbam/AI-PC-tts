# ChatTTS Fix Log

This file tracks all major bugs identified and the technical solutions implemented.

## [2026-05-16]
### 1. Twitch Bot Initialization Error
- **Issue**: `twitchio` 3.x removed support for anonymous IRC login, requiring `client_id` and `bot_id`.
- **Fix**: Replaced `twitchio` with a custom raw IRC socket collector using `justinfan` accounts.
- **Status**: Fixed & Stable.

### 2. Facebook "Site not supported" Error
- **Issue**: `chat-downloader` main class has a bug/breaking change that prevents it from recognizing `www.facebook.com` URLs even if the specific site module exists.
- **Fix**: Updated `facebook_collector.py` to use `FacebookChatDownloader` directly, bypassing the broken site detection logic. Refined URL extraction to handle `/username/videos/ID` format.
- **Status**: Fixed with direct class bypass (Monitoring for anti-bot measures).

### 3. TikTok "get_type" Error
- **Issue**: `TikTokLive` library throws `'str' object has no attribute 'get_type'` when parsing certain incoming events or during connection instability.
- **Fix**: Wrapped the comment handler in a specific try-except block and moved to `client.start()` with better async management.
- **Status**: Ongoing (Added more granular error catching).

### 4. Codebase Modularization
- **Issue**: Monolithic `engine.py` made debugging platform-specific issues difficult.
- **Fix**: Separated collectors into `youtube_collector.py`, `facebook_collector.py`, `twitch_collector.py`, and `tiktok_collector.py`.
- **Status**: Completed.

### 5. Enhanced Logging
- **Issue**: User needed easier access to logs for debugging.
- **Fix**: Implemented platform-specific log files (`logs/youtube.txt`, etc.) and a static `logs/log.txt`.
- **Status**: Completed.
