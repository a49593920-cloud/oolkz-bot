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
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/oollkz")

# Обложканы табу
if os.path.exists("music_cover.jpg"):
    COVER_PATH = "music_cover.jpg"
elif os.path.exists("music_cover.JPG"):
    COVER_PATH = "music_cover.JPG"
else:
    COVER_PATH = "music_cover.jpg"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "oolkz bot live!"
def run_flask():
    flask_app.run(host='0.0.0.0', port=10000)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 MP3 жібер! Мен обложка қойып берем - oollkz")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.audio.get_file() if update.message.audio else await update.message.document.get_file()
    path = f"temp_{file.file_id}.mp3"
    await file.download_to_drive(path)
    try:
        audio = MP3(path, ID3=ID3)
        title_text = str(audio.get("TIT2")) if audio.get("TIT2") else "oolkz music"
        artist_text = str(audio.get("TPE1")) if audio.get("TPE1") else "oolkz"
        
        thumb_buf = None
        cover_buf = None
        
        if os.path.exists(COVER_PATH):
            # Негізгі обложка
            base = Image.open(COVER_PATH).convert("RGB")
            img = base.resize((1280, 1280))
            
            # Текст үшін төменге қараңғы фон
            draw = ImageDraw.Draw(img, 'RGBA')
            draw.rectangle([(0, 950), (1280, 1280)], fill=(0,0,0,180))
            
            try:
                # Әдемі шрифт іздеу
                font_big = ImageFont.truetype("arial.ttf", 50)
                font_small = ImageFont.truetype("arial.ttf", 36)
            except:
                font_big = ImageFont.load_default()
                font_small = ImageFont.load_default()

            draw = ImageDraw.Draw(img)
            text = f"{artist_text} - {title_text}"[:45]
            draw.text((40, 980), text, fill="white", font=font_big, stroke_width=2, stroke_fill="black")
            draw.text((40, 1050), "t.me/oollkz", fill="#FFCC00", font=font_small, stroke_width=1, stroke_fill="black")

            cover_buf = io.BytesIO()
            img.save(cover_buf, format='JPEG', quality=95)
            cover_buf.seek(0)
            
            # Telegram үшін кіші thumbnail
            thumb = img.resize((320, 320))
            thumb_buf = io.BytesIO()
            thumb.save(thumb_buf, format='JPEG', quality=90)
            thumb_buf.seek(0)

        if audio.tags is None:
            audio.add_tags()
        audio.tags["TIT2"] = TIT2(encoding=3, text=title_text)
        audio.tags["TPE1"] = TPE1(encoding=3, text=artist_text)
        if cover_buf:
            audio.tags["APIC"] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=cover_buf.getvalue())
        audio.save()
        
        caption = f"🎧 {artist_text} - {title_text}\n\n{CHANNEL_URL}"
        if thumb_buf: thumb_buf.seek(0)
        
        await update.message.reply_audio(
            audio=open(path,'rb'), 
            caption=caption, 
            title=title_text, 
            performer=artist_text, 
            thumbnail=thumb_buf
        )
    except Exception as e:
        await update.message.reply_text(f"Қате: {e}")
    finally:
        if os.path.exists(path): os.remove(path)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.AUDIO | filters.Document.AUDIO, handle_audio))
    app.run_polling()
