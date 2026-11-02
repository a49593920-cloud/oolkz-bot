import os
import io
import threading
from flask import Flask
from telegram import Update, MessageEntity
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, APIC
from PIL import Image

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "@oollkz"
# .JPG, .jpg екеуін де таниды
def find_cover():
    for name in ["music_cover.JPG", "music_cover.jpg", "music_cover.jpeg", "music_cover.png"]:
        if os.path.exists(name):
            return name
    return "music_cover.JPG"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "oolkz live"
def run_flask(): flask_app.run(host='0.0.0.0', port=10000)

def get_cover():
    path = find_cover()
    img = Image.open(path).convert("RGB")
    w,h = img.size
    m = min(w,h)
    img = img.crop(((w-m)//2, (h-m)//2, (w-m)//2+m, (h-m)//2+m))
    img = img.resize((1280, 1280), Image.LANCZOS)
    cover_buf = io.BytesIO()
    img.save(cover_buf, format='JPEG', quality=95)
    cover_buf.seek(0)
    thumb_buf = io.BytesIO()
    img.resize((320,320), Image.LANCZOS).save(thumb_buf, format='JPEG', quality=90)
    thumb_buf.seek(0)
    return cover_buf, thumb_buf

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.audio.get_file() if update.message.audio else await update.message.document.get_file()
    path = f"temp_{file.file_id}.mp3"
    await file.download_to_drive(path)
    try:
        audio = MP3(path, ID3=ID3)
        title = str(audio.get("TIT2")) if audio.get("TIT2") else file.file_name.replace(".mp3","")
        artist = str(audio.get("TPE1")) if audio.get("TPE1") else "Unknown"
        title = title.strip()[:60] or "Track"
        artist = artist.strip()[:60] or "oollkz"
        if " - " in title:
            a,b = title.split(" - ", 1)
            if len(a) < 30:
                artist, title = a.strip(), b.strip()

        cover_buf, thumb_buf = get_cover()

        if audio.tags is None: audio.add_tags()
        audio.tags["TIT2"] = TIT2(encoding=3, text=title)
        audio.tags["TPE1"] = TPE1(encoding=3, text=artist)
        audio.tags["APIC"] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=cover_buf.getvalue())
        audio.save()

        caption_text = "oolkz"
        caption_entity = [MessageEntity(type=MessageEntity.TEXT_LINK, offset=0, length=5, url="https://t.me/oollkz")]

        with open(path, 'rb') as audio_file:
            data = audio_file.read()
        
        await update.message.reply_audio(
            audio=io.BytesIO(data),
            title=title, performer=artist,
            thumbnail=thumb_buf,
            caption=caption_text,
            caption_entities=caption_entity
        )
        thumb_buf.seek(0)
        await context.bot.send_audio(
            chat_id=CHANNEL,
            audio=io.BytesIO(data),
            title=title, performer=artist,
            thumbnail=thumb_buf,
            caption=caption_text,
            caption_entities=caption_entity
        )
    except Exception as e:
        await update.message.reply_text(f"Қате: {e}")
    finally:
        if os.path.exists(path): os.remove(path)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.AUDIO | filters.Document.AUDIO, handle_audio))
    app.run_polling()
