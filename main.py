import os, io, logging
from threading import Thread
from flask import Flask
from PIL import Image
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, APIC
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from telegram.constants import ParseMode

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = "@oollkz"  # каналың
CHANNEL_LINK = "https://t.me/oollkz" # басқанда осыған лақтырады
COVER_PATH = "music_cover.JPG"

logging.basicConfig(level=logging.INFO)
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "oolkz live"

def get_cover():
    img = Image.open(COVER_PATH).convert("RGB").resize((800,800))
    b1, b2 = io.BytesIO(), io.BytesIO()
    img.save(b1, format="JPEG", quality=95)
    img.save(b2, format="JPEG", quality=95)
    b1.seek(0); b2.seek(0)
    return b1, b2

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ән жібер!")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    file_obj = msg.audio or msg.document
    if not file_obj:
        return

    await msg.reply_text("🔄 Өңдеп жатырмын...")
    path = f"temp_{file_obj.file_id}.tmp"
    
    try:
        tg_file = await context.bot.get_file(file_obj.file_id)
        await tg_file.download_to_drive(path)

        title = "Жүрегім"
        artist = "RK"
        if msg.audio:
            if msg.audio.title: title = msg.audio.title.strip()[:60]
            if msg.audio.performer: artist = msg.audio.performer.strip()[:60]
        
        # Егер басқа ән болса, сол әннің атын алады, бірақ формат сақталады
        # Егер тек RK - Журегим керек болса, жоғарыдағы 2 жолды өшір

        cover_buf, thumb_buf = get_cover()

        try:
            audio = MP3(path, ID3=ID3)
            if audio.tags is None: audio.add_tags()
            audio.tags["TIT2"] = TIT2(encoding=3, text=title)
            audio.tags["TPE1"] = TPE1(encoding=3, text=artist)
            audio.tags["APIC"] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=cover_buf.getvalue())
            audio.save()
        except:
            pass

        # МІНЕ, СЕН ҚАЛАҒАН ЖАЗУ — БАССАҢ КАНАЛҒА ЛАҚТЫРАДЫ
        caption_with_link = f'<a href="{CHANNEL_LINK}">oolkz</a>'

        # Саған
        with open(path, "rb") as f:
            await msg.reply_audio(
                audio=f, title=title, performer=artist,
                thumbnail=thumb_buf, caption=caption_with_link,
                parse_mode=ParseMode.HTML
            )
        
        # Каналға
        _, thumb_buf2 = get_cover()
        with open(path, "rb") as f2:
            await context.bot.send_audio(
                chat_id=CHANNEL_ID, audio=f2,
                title=title, performer=artist,
                thumbnail=thumb_buf2, caption=caption_with_link,
                parse_mode=ParseMode.HTML
            )

    except Exception as e:
        logging.error(e)
        await msg.reply_text(f"Қате: {e}")
    finally:
        if os.path.exists(path): os.remove(path)

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.AUDIO | filters.Document.ALL, handle_audio))
    app.run_polling()
