import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# Render.com yoki xavfsiz muhitdan o'qib oladi
API_ID = int(os.environ.get("API_ID", 34514256))
API_HASH = os.environ.get("API_HASH", "c043c45b653d15be7bf421b0b770f887")
SESSION_STRING = os.environ.get("SESSION_STRING", "")
TARGET_CHANNEL = int(os.environ.get("TARGET_CHANNEL", -1004327281879))

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(incoming=True))
async def interceptor(event):
    if not event.out:
        try:
            await event.forward_to(TARGET_CHANNEL)
        except Exception as e:
            print(f"Xatolik yuz berdi: {e}")

if __name__ == '__main__':
    print("Userbot ishga tushdi va xabarlarni kanalga saqlamoqda...")
    client.start()
    client.run_until_disconnected()
