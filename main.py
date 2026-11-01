import os
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "@oollkz"

def make_thumb():
    for name in ["music_cover.JPG", "music_cover.jpg"]:
        if os.path.exists(name):
            img = Image.open(name).convert("RGB")
            w,h = img.size
            m = min(w,h)
            img = img.crop(((w-m)//2, (h-m)//2, (w-m)//2+m, (h-m)//2+m))
            img = img.resize((320,320))
            img.save("thumb.jpg", quality=80, optimize=True)
            return "thumb.jpg"
    return None

def clean(s):
    if not s: return ""
    s = s.strip()
    for ext in [".wav",".mp3",".m4a",".flac",".ogg"]:
        if s.lower().endswith(ext):
            s = s[:-len(ext)]
    return s.strip()

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    audio = update.message.audio or update.message.document
    if not audio: return

    title = clean(audio.file_name or "Track")
    performer = "oollkz"
    if update.message.audio:
        if update.message.audio.title: title = clean(update.message.audio.title)
        if update.message.audio.performer: performer = clean(update.message.audio.performer)

    if " - " in title and performer == "oollkz":
        a,b = title.split(" - ",1)
        performer, title = a.strip(), b.strip()

    context.user_data["last"] = (audio.file_id, title, performer)

    thumb = make_thumb()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Каналға жіберу", callback_data="go")],
        [InlineKeyboardButton("❌ Болдырмау", callback_data="no")],
        [InlineKeyboardButton("oolkz", url="https://t.me/oollkz")]
    ])

    if thumb:
        with open(thumb,'rb') as t:
            await context.bot.send_audio(update.effective_chat.id, audio.file_id, thumbnail=t, title=title, performer=performer, caption="", reply_markup=kb)
    else:
        await context.bot.send_audio(update.effective_chat.id, audio.file_id, title=title, performer=performer, caption="", reply_markup=kb)

async def on_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "no":
        await q.delete_message()
        return
    file_id, title, performer = context.user_data.get("last", (None,None,None))
    if not file_id: return
    thumb = make_thumb()
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("oolkz", url="https://t.me/oollkz")]])
    if thumb:
        with open(thumb,'rb') as t:
            await context.bot.send_audio(CHANNEL, file_id, thumbnail=t, title=title, performer=performer, caption="", reply_markup=kb)
    else:
        await context.bot.send_audio(CHANNEL, file_id, title=title, performer=performer, caption="", reply_markup=kb)
    await q.edit_message_text(f"✅ Каналға кетті: {performer} - {title}")

app = Application.builder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.AUDIO | filters.Document.ALL, handle_audio))
app.add_handler(CallbackQueryHandler(on_btn))

from flask import Flask
f = Flask(__name__)
@f.route('/')
def h(): return "ok"

if __name__ == '__main__':
    import threading
    threading.Thread(target=lambda: f.run(host='0.0.0.0', port=10000)).start()
    app.run_polling()
