import os, io, re, logging, asyncio
from threading import Thread
from flask import Flask
from PIL import Image
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, TIT2, TPE1, APIC
from mutagen.mp4 import MP4
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from telegram.constants import ParseMode
import yt_dlp

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = "@oollkz"
CHANNEL_LINK = "https://t.me/oollkz"
COVER_PATH = "music_cover.JPG"

logging.basicConfig(level=logging.INFO)
flask_app = Flask(__name__)

@flask_app.route('/')
def home(): return "oolkz live"

def get_cover():
    img = Image.open(COVER_PATH).convert("RGB").resize((800,800))
    b1, b2 = io.BytesIO(), io.BytesIO()
    img.save(b1, format="JPEG", quality=95)
    img.save(b2, format="JPEG", quality=95)
    b1.seek(0); b2.seek(0)
    return b1, b2

def download_from_link(url, temp_id):
    output = f"temp_{temp_id}"
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': f"{output}.%(ext)s",
        'quiet': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'Track')[:100]
        artist = info.get('uploader', 'Unknown')[:100]
        # файлды табу
        for file in os.listdir("."):
            if file.startswith(output):
                return file, title, artist
    return None, "Track", "Unknown"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Әннің линкін жібер! 🎵\nyoutube.com / youtu.be / song.link")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not any(x in url for x in ["youtube.com", "youtu.be", "song.link", "music.youtube"]):
        return
    status = await update.message.reply_text("🔄 Жүктеп жатырмын...")
    path = None
    try:
        loop = asyncio.get_event_loop()
        path, title, artist = await loop.run_in_executor(None, download_from_link, url, update.message.message_id)
        if not path or not os.path.exists(path):
            await status.edit_text("Жүктей алмадым 😥 басқа линк жіберіңіз")
            return

        caption = f'<a href="{CHANNEL_LINK}">oolkz</a>'
        cover_buf, thumb_buf = get_cover()

        with open(path, "rb") as f:
            await update.message.reply_audio(audio=f, title=title, performer=artist, thumbnail=thumb_buf, caption=caption, parse_mode=ParseMode.HTML)
        _, thumb_buf2 = get_cover()
        with open(path, "rb") as f2:
            await context.bot.send_audio(chat_id=CHANNEL_ID, audio=f2, title=title, performer=artist, thumbnail=thumb_buf2, caption=caption, parse_mode=ParseMode.HTML)
        await status.delete()
    except Exception as e:
        await status.edit_text(f"Қате: {e}")
    finally:
        if path and os.path.exists(path): os.remove(path)
        for f in os.listdir("."):
            if f.startswith(f"temp_{update.message.message_id}"):
                try: os.remove(f)
                except: pass

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    file_obj = msg.audio or msg.document
    if not file_obj: return
    if file_obj.file_size > 20 * 1024 * 1024:
        await msg.reply_text("Бұл файл 20MB-тан үлкен 😥 Линкін жіберіңіз")
        return
    await msg.reply_text("✅ Бұл файлды өңдеу бұрынғыдай")

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.AUDIO | filters.Document.ALL, handle_audio))
    app.run_polling()
