import os, io, logging
from threading import Thread
from flask import Flask
from PIL import Image
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, APIC

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = "@oollkz"  # сенің каналын
COVER_PATH = "music_cover.JPG"

logging.basicConfig(level=logging.INFO)
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "oolkz live"

def get_cover():
    img = Image.open(COVER_PATH).convert("RGB").resize((800,800))
    buf1 = io.BytesIO()
    buf2 = io.BytesIO()
    img.save(buf1, format="JPEG", quality=95)
    img.save(buf2, format="JPEG", quality=95)
    buf1.seek(0)
    buf2.seek(0)
    return buf1, buf2

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ән жібер! Басқа каналдан forward қылсаң да болады!")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    file_obj = msg.audio or msg.document
    if not file_obj:
        return

    await msg.reply_text("🔄 Өңдеп жатырмын...")
    path = f"temp_{file_obj.file_id}.mp3"
    
    try:
        tg_file = await context.bot.get_file(file_obj.file_id)
        await tg_file.download_to_drive(path)

        # Аты-жөнін алуға тырысамыз
        raw_title = file_obj.file_name or file_obj.title or "Track"
        raw_title = raw_title.replace(".mp3","").replace(".m4a","")[:60]
        artist = "oollkz"
        title = raw_title

        if " - " in raw_title:
            a,b = raw_title.split(" - ", 1)
            artist, title = a.strip()[:40], b.strip()[:60]

        cover_buf, thumb_buf = get_cover()

        # Тег жазуға тырысамыз, болмаса да өтеміз
        try:
            audio = MP3(path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            audio.tags["TIT2"] = TIT2(encoding=3, text=title)
            audio.tags["TPE1"] = TPE1(encoding=3, text=artist)
            audio.tags["APIC"] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=cover_buf.getvalue())
            audio.save()
        except Exception as e:
            logging.warning(f"ID3 жаза алмадым: {e}")

        # 1. Саған қайтару
        with open(path, "rb") as f:
            await msg.reply_audio(
                audio=f,
                title=title,
                performer=artist,
                thumbnail=thumb_buf,
                caption=f"✅ Дайын: {artist} - {title}"
            )
        
        # 2. Каналға салу
        cover_buf2, thumb_buf2 = get_cover()
        with open(path, "rb") as f2:
            await context.bot.send_audio(
                chat_id=CHANNEL_ID,
                audio=f2,
                title=title,
                performer=artist,
                thumbnail=thumb_buf2,
                caption=f"{artist} - {title}"
            )

    except Exception as e:
        logging.error(e)
        await msg.reply_text(f"Қате: {e}")
    finally:
        if os.path.exists(path):
            os.remove(path)

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    # ЕНДІ ЛЮБОЙ АУДИОҒА ЖАУАП БЕРЕДІ
    app.add_handler(MessageHandler(filters.AUDIO | filters.Document.ALL, handle_audio))
    logging.info("Bot polling started...")
    app.run_polling()
