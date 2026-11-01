import os, io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, APIC
from PIL import Image, ImageDraw, ImageFont
from flask import Flask
import threading

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "@oollkz"
COVER_PATH = "music_cover.jpg"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "oolkz bot live!"
def run_flask(): flask_app.run(host='0.0.0.0', port=10000)

def make_cover(title, artist):
    # EXACT background
    base = Image.open(COVER_PATH).convert("RGB")
    w,h = base.size
    m = min(w,h)
    base = base.crop(((w-m)//2, (h-m)//2, (w-m)//2+m, (h-m)//2+m))
    img = base.resize((1280, 1280), Image.LANCZOS)
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 80)
        font_artist = ImageFont.truetype("arial.ttf", 55)
        font_oolkz = ImageFont.truetype("arial.ttf", 42)
    except:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        font_artist = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 55)
        font_oolkz = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)

    # Only TITLE and ARTIST in center
    tb = draw.textbbox((0,0), title, font=font_title, stroke_width=6)
    ab = draw.textbbox((0,0), f"— {artist}", font=font_artist, stroke_width=4)
    x1 = (1280 - (tb[2]-tb[0]))//2
    x2 = (1280 - (ab[2]-ab[0]))//2

    draw.text((x1, 760), title, fill="white", font=font_title, stroke_width=7, stroke_fill="black")
    draw.text((x2, 860), f"— {artist}", fill="white", font=font_artist, stroke_width=5, stroke_fill="black")

    # Bottom left small oolkz on image - as you asked
    draw.text((40, 1200), "oolkz", fill="white", font=font_oolkz, stroke_width=4, stroke_fill="black")

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
        title = str(audio.get("TIT2")) if audio.get("TIT2") else file.file_name
        artist = str(audio.get("TPE1")) if audio.get("TPE1") else "Блатной Проспект"
        title = title.replace(".mp3","").replace(".wav","")[:40]
        artist = artist[:50]

        cover_buf, thumb_buf = make_cover(title, artist)

        if audio.tags is None: audio.add_tags()
        audio.tags["TIT2"] = TIT2(encoding=3, text=title)
        audio.tags["TPE1"] = TPE1(encoding=3, text=artist)
        audio.tags["APIC"] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=cover_buf.getvalue())
        audio.save()

        # Clickable oolkz that leads to channel
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("oolkz", url="https://t.me/oollkz")]])

        await update.message.reply_audio(
            audio=open(path,'rb'),
            title=title, performer=artist,
            caption=f"{title} — {artist}",
            thumbnail=thumb_buf,
            reply_markup=keyboard
        )
        await context.bot.send_audio(
            chat_id=CHANNEL,
            audio=open(path,'rb'),
            title=title, performer=artist,
            caption=f"{title} — {artist}",
            thumbnail=thumb_buf,
            reply_markup=keyboard
        )
    finally:
        if os.path.exists(path): os.remove(path)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.AUDIO | filters.Document.AUDIO, handle_audio))
    app.run_polling()
