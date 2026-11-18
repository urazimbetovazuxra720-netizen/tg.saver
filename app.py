import os
import threading
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot 24/7 ishlayapti!"

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STRING = "1ApWapzMBuxDZrCnQY8-N4JvZCSWEWJayHuV80ECSZyAB_PKa868uOvg6YXaNxauImKm5fyy61Ad2sIQHAIoEYTkoxdmdzSj_xdLAWryZKFwuWhkA6GUqX3ao783og02i9ewcBY7gJbnCabQT0Jb0rI-WNi-ni4SGcp_2Owu7Y81pZHbQCgSPQjXibjcjG1sn6xcpz5-cOHIGGq_jJ8ui2zzXVd62-8vHIr7gZeYOpMd88b_RbyQFww2uzcqy4vpsF9zpE1dL7QYEus6RtUemjCGPT_v2SSMdzf1EH7bu9SCBKLXSXE11zpwthsmFjU0BawXIHj3d1lEhG0YJ6BO1DU9j7MNpneg="

TARGET_CHANNEL = int(os.environ.get("TARGET_CHANNEL", 0))

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

message_history = {}

def get_msg_time(message_date=None):
    tz = ZoneInfo("Asia/Tashkent")
    if message_date:
        return message_date.astimezone(tz).strftime("%H:%M")
    return datetime.now(tz).strftime("%H:%M")

# 1. Yangi kelgan xabarlar
@client.on(events.NewMessage(incoming=True))
async def new_message_handler(event):
    if not event.out:
        try:
            # Media fayllar bo'lsa o'zini forward qilamiz
            if event.media and not event.raw_text:
                await event.forward_to(TARGET_CHANNEL)
                return

            chat = await event.get_chat()
            sender = await event.get_sender()
            
            chat_title = getattr(chat, 'title', None)
            is_channel = getattr(chat, 'broadcast', False)
            
            sender_name = "Noma'lum"
            if sender:
                if hasattr(sender, 'first_name') and sender.first_name:
                    sender_name = f"{sender.first_name} {sender.last_name or ''}".strip()
                elif hasattr(sender, 'title') and sender.title:
                    sender_name = sender.title

            if is_channel:
                source_type = "Kanal"
            elif chat_title:
                source_type = f"Guruh: {chat_title}"
            else:
                source_type = "Shaxsiy chat"

            msg_time = get_msg_time(event.message.date)
            text = event.raw_text

            message_history[event.id] = {
                "sender_name": sender_name,
                "source_type": source_type,
                "history": [{"text": text, "time": msg_time}]
            }

            # Xabar birinchi o'ringa qo'yildi
            out_text = (
                f"📬 **Yangi xabar:** {text} `[{msg_time}]`\n\n"
                f"👤 **Kimdan:** {sender_name}\n"
                f"💬 **Qayerdan:** {source_type}"
            )
            
            await client.send_message(TARGET_CHANNEL, out_text)
        except Exception as e:
            print(f"Xatolik (New): {e}")

# 2. Tahrirlangan xabarlar
@client.on(events.MessageEdited(incoming=True))
async def edited_message_handler(event):
    if not event.out:
        try:
            msg_id = event.id
            new_text = event.raw_text
            if not new_text:
                return
            
            edit_time = get_msg_time(event.message.date)

            if msg_id not in message_history:
                sender = await event.get_sender()
                chat = await event.get_chat()
                sender_name = getattr(sender, 'first_name', 'Noma\'lum') if sender else 'Noma\'lum'
                chat_title = getattr(chat, 'title', 'Shaxsiy chat')
                message_history[msg_id] = {
                    "sender_name": sender_name,
                    "source_type": chat_title,
                    "history": [{"text": "Topilmadi", "time": edit_time}]
                }

            data = message_history[msg_id]
            data["history"].append({"text": new_text, "time": edit_time})

            history_lines = []
            hist_list = data["history"]
            
            for i, h in enumerate(hist_list):
                if i == 0:
                    history_lines.append(f"🔹 **Asl xabar:** {h['text']} `[{h['time']}]`")
                elif i == len(hist_list) - 1:
                    history_lines.append(f"🔸 **Oxirgi holat:** {h['text']} `[{h['time']}]`")
                else:
                    history_lines.append(f"🔸 **{i}-tahrir:** {h['text']} `[{h['time']}]`")

            history_text = "\n".join(history_lines)

            out_text = (
                f"✏️ **Tahrirlangan xabar tarixi:**\n\n"
                f"👤 **Kimdan:** {data['sender_name']}\n"
                f"💬 **Chat/Guruh:** {data['source_type']}\n\n"
                f"{history_text}"
            )

            await client.send_message(TARGET_CHANNEL, out_text)
        except Exception as e:
            print(f"Xatolik (Edited): {e}")

# 3. O'chirilgan xabarlar
@client.on(events.MessageDeleted())
async def deleted_message_handler(event):
    try:
        for msg_id in event.deleted_ids:
            if msg_id in message_history:
                data = message_history[msg_id]
                last_text = data["history"][-1]["text"]
                del_time = get_msg_time()

                out_text = (
                    f"🗑️ **O'chirilgan xabar:** {last_text} `[{del_time}]`\n\n"
                    f"👤 **Kimdan:** {data['sender_name']}\n"
                    f"💬 **Qayerdan:** {data['source_type']}"
                )
                await client.send_message(TARGET_CHANNEL, out_text)
                del message_history[msg_id]
    except Exception as e:
        print(f"Xatolik (Deleted): {e}")

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    print("Userbot Render serverida ishga tushdi...")
    client.start()
    client.run_until_disconnected()
