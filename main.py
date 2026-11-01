import os
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "@oollkz"

def make_thumb():
    for name in ["music_cover.JPG", "music_cover.jpg", "base.jpg"]:
        if os.path.exists(name):
            img = Image.open(name).convert("RGB")
            img = img.resize((320, 320))
            img.save("thumb.jpg", quality=95)
            return "thumb.jpg"
    return None

def clean_name(name: str):
    if not name: return "Track"
    for ext in [".mp3",".wav",".m4a",".flac",".ogg",".MP3",".WAV",".WAV"]:
        if name.lower().endswith(ext.lower()):
            name = name[:-len(ext)]
    return name.strip()

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    audio = msg.audio or msg.document
    if not audio: return

    raw_title = msg.audio.title if msg.audio and msg.audio.title else audio.file_name
    raw_performer = msg.audio.performer if msg.audio and msg.audio.performer else "oollkz"

    title = clean_name(raw_title)
    performer = clean_name(raw_performer)
    if " - " in title and performer == "oollkz":
        p = title.split(" - ", 1)
        performer, title = p[0].strip(), p[1].strip()

    # Сақтап қоямыз
    context.user_data["last_audio"] = {
        "file_id": audio.file_id,
        "title": title,
        "performer": performer
    }

    thumb_path = make_thumb()
    
    # Саған превью
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Каналға жіберу", callback_data="publish")],
        [InlineKeyboardButton("❌ Болдырмау", callback_data="cancel")],
        [InlineKeyboardButton("oolkz", url="https://t.me/oollkz")]
    ])

    if thumb_path:
        with open(thumb_path, 'rb') as t:
            await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=audio.file_id,
                thumbnail=t,
                title=title,
                performer=performer,
                caption=f"Превью: {performer} - {title}\nФото: өз фотоңмен",
                reply_markup=keyboard
            )
    else:
        await msg.reply_text("⚠️ Фото табылмады! music_cover.JPG жүктелмеген", reply_markup=keyboard)

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = context.user_data.get("last_audio")
    if not data:
        await query.edit_message_text("Файл табылмады, қайта жібер")
        return

    if query.data == "cancel":
        await query.edit_message_text("❌ Болдырылмады")
        return

    if query.data == "publish":
        thumb_path = make_thumb()
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("oolkz", url="https://t.me/oollkz")]
        ])
        if thumb_path:
            with open(thumb_path, 'rb') as t:
                await context.bot.send_audio(
                    chat_id=CHANNEL,
                    audio=data["file_id"],
                    thumbnail=t,
                    title=data["title"],
                    performer=data["performer"],
                    caption="",
                    reply_markup=keyboard
                )
        else:
            await context.bot.send_audio(
                chat_id=CHANNEL,
                audio=data["file_id"],
                title=data["title"],
                performer=data["performer"],
                caption="",
                reply_markup=keyboard
            )
        await query.edit_message_text(f"✅ Каналға кетті: {data['performer']} - {data['title']}")

app = Application.builder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.AUDIO | filters.Document.ALL, handle_audio))
app.add_handler(CallbackQueryHandler(on_button))

from flask import Flask
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot live"

if __name__ == '__main__':
    import threading
    threading.Thread(target=lambda: flask_app.run(host='0.0.0.0', port=10000)).start()
    app.run_polling()
