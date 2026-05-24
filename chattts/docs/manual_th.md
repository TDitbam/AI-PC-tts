# คู่มือการใช้งาน ChatTTS

โปรแกรมนี้ใช้ดึงข้อความจาก `YouTube Live`, `Twitch Chat` และ `TikTok Live` แล้วแปลงเป็นเสียงพูดภาษาไทยอัตโนมัติ

## เริ่มต้นใช้งาน

### GUI

รัน:

```bash
python start_gui.py
```

จากนั้น:

1. เปิดแพลตฟอร์มที่ต้องการใช้งาน
2. ใส่ `YouTube URL/ID`, `Twitch channel` หรือ `TikTok @username`
3. เลือกเสียงและตั้งค่า delay
4. กด `START SYSTEM`

### CLI

ตั้งค่าใน `config.ini` แล้วรัน:

```bash
python start_cli.py
```

## ไฟล์ log

ไฟล์ log จะอยู่ในโฟลเดอร์ `logs/`:

- `log.txt`
- `youtube.txt`
- `twitch.txt`
- `tiktok.txt`

## หมายเหตุรายแพลตฟอร์ม

- `YouTube`: รองรับทั้ง URL และ Video ID
- `Twitch`: ใช้ anonymous IRC login จึงไม่ต้องใช้ API key
- `TikTok`: อาจมี reconnect หรือ error จากไลบรารี `TikTokLive` เป็นครั้งคราว ระบบจะพยายามเชื่อมต่อใหม่ให้อัตโนมัติ

## โครงสร้างหลัก

- `start_gui.py`: โปรแกรมหน้าจอ
- `start_cli.py`: โปรแกรมแบบ command line
- `core/tts_engine.py`: ตัวควบคุมหลัก
- `core/yt_chat.py`: ตัวดึงแชท YouTube
- `core/twitch_chat.py`: ตัวดึงแชท Twitch
- `core/tiktok_chat.py`: ตัวดึงแชท TikTok
