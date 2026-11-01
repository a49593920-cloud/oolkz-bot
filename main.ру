import os
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "@oollkz"

def get_cover_file():
    # Сенің файлың music_cover.JPG деп тұр, соны қолданамыз
    for name in ["music_cover.JPG", "music_cover.jpg", "base.jpg", "cover.jpg"]:
        if os.path.exists(name):
            return name
    return None

def make_thumb():
    cover_file = get_cover_file()
    if not cover_file:
        return None
    base = Image.open(cover_file).convert("RGB")
    # Фотоны өзгертпейміз, тек 320x320 thumbnail
    thumb = base.resize((320, 320))
    thumb.save("thumb.jpg", quality=95)
    return "thumb.jpg"

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    audio = msg.audio or msg.document
    if not audio:
        return

    title = audio.file_name or "Track"
    performer = "oollkz"
    if msg.audio:
        if msg.audio.title: title = msg.audio.title
        if msg.audio.performer: performer = msg.audio.performer

    thumb_path = make_thumb()
    
    # Астында көк жазу - басқанда каналға
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("oolkz", url="https://t.me/oollkz")]
    ])

    if thumb_path:
        with open(thumb_path, 'rb') as thumb:
            await context.bot.send_audio(
                chat_id=CHANNEL,
                audio=audio.file_id,
                thumbnail=thumb,
                title=title,
                performer=performer,
                caption=f"{performer} - {title}",
                reply_markup=keyboard
            )
    else:
        await context.bot.send_audio(
            chat_id=CHANNEL,
            audio=audio.file_id,
            title=title,
            performer=performer,
            caption=f"{performer} - {title}",
            reply_markup=keyboard
        )
    
    await msg.reply_text(f"✅ Дайын: {title}")

app = Application.builder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.AUDIO | filters.Document.ALL, handle_audio))

from flask import Flask
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot live"

if __name__ == '__main__':
    import threading
    threading.Thread(target=lambda: flask_app.run(host='0.0.0.0', port=10000)).start()
    app.run_polling()
