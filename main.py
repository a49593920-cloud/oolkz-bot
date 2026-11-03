import os, io, logging, asyncio, requests
from threading import Thread
from flask import Flask
from PIL import Image
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, APIC
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
        'extractor_args': {'youtube': {'player_client': ['android_music', 'android', 'ios']}},
        'nocheckcertificate': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Track')[:100]
            artist = info.get('uploader', 'Unknown')[:100]
            for f in os.listdir("."):
                if f.startswith(output):
                    return f, title, artist
    except Exception as e:
        print(f"yt-dlp failed: {e}")
        cobalt_instances = [
            "https://api.cobalt.tools/",
            "https://co.wuk.sh/api/json",
            "https://cobalt-api.ahmedbna.com/",
        ]
        for api_url in cobalt_instances:
            try:
                print(f"Trying cobalt: {api_url}")
                r = requests.post(api_url,
                    json={"url": url, "aFormat": "mp3", "isAudioOnly": True},
                    headers={"Accept": "application/json", "Content-Type": "application/json"},
                    timeout=30).json()
                audio_url = r.get("url")
                if audio_url:
                    file_path = f"{output}.mp3"
                    with requests.get(audio_url, stream=True, timeout=60) as rr:
                        rr.raise_for_status()
                        with open(file_path, 'wb') as f:
                            for chunk in rr.iter_content(8192):
                                f.write(chunk)
                    return file_path, "Track", "Unknown"
            except Exception as e2:
                print(f"Failed {api_url}: {e2}")
                continue
        raise e
    return None, "Track", "Unknown"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Әннің линкін жібер! 🎵")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not any(x in url for x in ["youtube.com", "youtu.be", "song.link", "music.youtube", "youtu"]):
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
        await msg.reply_text("20MB-тан үлкен 😥 линкін жіберіңіз")
        return
    status = await msg.reply_text("🔄 Өңдеп жатырмын...")
    path = f"temp_{file_obj.file_id}.tmp"
    try:
        tg_file = await context.bot.get_file(file_obj.file_id)
        await tg_file.download_to_drive(path)
        title = "Track"; artist = "Unknown"
        if msg.audio:
            title = msg.audio.title or "Track"
            artist = msg.audio.performer or "Unknown"
        elif file_obj.file_name:
            clean = file_obj.file_name.replace(".mp3","")
            if " - " in clean:
                a,b = clean.split(" - ",1)
                artist, title = a.strip(), b.strip()
            else: title = clean
        cover_buf, thumb_buf = get_cover()
        try:
            audio = MP3(path, ID3=ID3)
            if audio.tags is None: audio.add_tags()
            audio.tags["TIT2"] = TIT2(encoding=3, text=title)
            audio.tags["TPE1"] = TPE1(encoding=3, text=artist)
            audio.tags["APIC"] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=cover_buf.getvalue())
            audio.save()
        except: pass
        caption = f'<a href="{CHANNEL_LINK}">oolkz</a>'
        with open(path, "rb") as f:
            await msg.reply_audio(audio=f, title=title, performer=artist, thumbnail=thumb_buf, caption=caption, parse_mode=ParseMode.HTML)
        _, thumb_buf2 = get_cover()
        with open(path, "rb") as f2:
            await context.bot.send_audio(chat_id=CHANNEL_ID, audio=f2, title=title, performer=artist, thumbnail=thumb_buf2, caption=caption, parse_mode=ParseMode.HTML)
        await status.delete()
    except Exception as e:
        await status.edit_text(f"Қате: {e}")
    finally:
        if os.path.exists(path): os.remove(path)

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.AUDIO | filters.Document.ALL, handle_audio))
    app.run_polling()
