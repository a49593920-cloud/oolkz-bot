import os
import io
import threading
from flask import Flask
from telegram import Update, MessageEntity
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, APIC
from PIL import Image

# Токен Render-дағы Environment-дан келеді
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "@oollkz"  # Каналың
COVER_PATH = "music_cover.jpg"  # Фоның

# Render үшін сайт
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "oolkz bot live"
def run_flask():
    flask_app.run(host='0.0.0.0', port=10000)

def get_cover():
    # Фонға ЕШТЕҢЕ жазбайды, тура фото
    img = Image.open(COVER_PATH).convert("RGB")
    w, h = img.size
    m = min(w, h)
    # Квадрат қыламыз
    img = img.crop(((w - m) // 2, (h - m) // 2, (w - m) // 2 + m, (h - m) // 2 + m))
    img = img.resize((1280, 1280), Image.LANCZOS)

    cover_buf = io.BytesIO()
    img.save(cover_buf, format='JPEG', quality=95)
    cover_buf.seek(0)

    thumb_buf = io.BytesIO()
    img.resize((320, 320), Image.LANCZOS).save(thumb_buf, format='JPEG', quality=90)
    thumb_buf.seek(0)

    return cover_buf, thumb_buf

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.audio.get_file() if update.message.audio else await update.message.document.get_file()
    path = f"temp_{file.file_id}.mp3"
    await file.download_to_drive(path)

    try:
        audio = MP3(path, ID3=ID3)
        title = str(audio.get("TIT2")) if audio.get("TIT2") else file.file_name.replace(".mp3", "")
        artist = str(audio.get("TPE1")) if audio.get("TPE1") else "Unknown"
        title = title.strip()[:60] or "Track"
        artist = artist.strip()[:60] or "oollkz"

        if " - " in title:
            a, b = title.split(" - ", 1)
            if len(a) < 30:
                artist, title = a.strip(), b.strip()

        cover_buf, thumb_buf = get_cover()

        if audio.tags is None:
            audio.add_tags()
        audio.tags["TIT2"] = TIT2(encoding=3, text=title)
        audio.tags["TPE1"] = TPE1(encoding=3, text=artist)
        audio.tags["APIC"] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=cover_buf.getvalue())
        audio.save()

        # Астындағы көк oolkz - басқанда каналыңа кетеді
        caption_text = "oolkz"
        caption_entity = [MessageEntity(type=MessageEntity.TEXT_LINK, offset=0, length=5, url="https://t.me/oollkz")]

        # 1. Саған жібереді
        await update.message.reply_audio(
            audio=open(path, 'rb'),
            title=title,
            performer=artist,
            thumbnail=thumb_buf,
            caption=caption_text,
            caption_entities=caption_entity
        )

        # 2. Каналға жібереді
        await context.bot.send_audio(
            chat_id=CHANNEL,
            audio=open(path, 'rb'),
            title=title,
            performer=artist,
            thumbnail=thumb_buf,
            caption=caption_text,
            caption_entities=caption_entity
        )

    except Exception as e:
        await update.message.reply_text(f"Қате: {e}")
    finally:
        if os.path.exists(path):
            os.remove(path)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.AUDIO | filters.Document.AUDIO, handle_audio))
    app.run_polling()
