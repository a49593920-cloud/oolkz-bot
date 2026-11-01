import os
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, APIC
from PIL import Image, ImageDraw, ImageFont
import io
from flask import Flask
import threading

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/oolkz")
COVER_PATH = "music_cover.jpg"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "oolkz bot live!"
def run_flask():
    flask_app.run(host='0.0.0.0', port=10000)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("MP3 жібер!")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.audio.get_file() if update.message.audio else await update.message.document.get_file()
    path = f"temp_{file.file_id}.mp3"
    await file.download_to_drive(path)
    try:
        audio = MP3(path, ID3=ID3)
        title_text = str(audio.get("TIT2")) if audio.get("TIT2") else "oolkz music"
        artist_text = str(audio.get("TPE1")) if audio.get("TPE1") else "oolkz"
        thumb_buf = None
        if os.path.exists(COVER_PATH):
            img = Image.open(COVER_PATH).convert("RGB").resize((800,800))
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            draw.text((30,700), f"{artist_text} - {title_text}"[:40], fill="white", font=font, stroke_width=3, stroke_fill="black")
            thumb_buf = io.BytesIO()
            img.save(thumb_buf, format='JPEG')
            thumb_buf.seek(0)
        if audio.tags is None:
            audio.add_tags()
        audio.tags["TIT2"] = TIT2(encoding=3, text=title_text)
        audio.tags["TPE1"] = TPE1(encoding=3, text=artist_text)
        if thumb_buf:
            audio.tags["APIC"] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=thumb_buf.getvalue())
        audio.save()
        caption = f"{artist_text} - {title_text}\n\n{CHANNEL_URL}"
        if thumb_buf: thumb_buf.seek(0)
        await update.message.reply_audio(audio=open(path,'rb'), caption=caption, title=title_text, performer=artist_text, thumbnail=thumb_buf)
    finally:
        if os.path.exists(path): os.remove(path)

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.AUDIO | filters.Document.AUDIO, handle_audio))
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app.run_polling()
