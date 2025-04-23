import os
import re
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from database import get_db
from flask import Flask  # NUEVO: Importar Flask
from threading import Thread  # NUEVO: Importar Thread

# NUEVO: Configurar servidor Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "¡Bot activo! 🚀"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

TOKEN = os.environ.get("TELEGRAM_TOKEN")
COLLECTION = get_db()

# Función para guardar mensajes del canal
def save_post(update: Update, context: CallbackContext):
    message = update.channel_post or update.edited_channel_post

    if message and message.photo and message.caption:
        hashtags = re.findall(r"#(\w+)", message.caption)
        if not hashtags:
            return

        post = {
            "hashtags": [tag.lower() for tag in hashtags],
            "cover": message.photo[-1].file_id,
            "synopsis": message.caption,
            "files": [],
            "main_message_id": message.message_id
        }
        COLLECTION.insert_one(post)

    elif message and message.reply_to_message:
        main_post = COLLECTION.find_one({"main_message_id": message.reply_to_message.message_id})
        if not main_post:
            return

        file_info = None
        if message.document:
            file_info = {"type": "document", "file_id": message.document.file_id}
        elif message.video:
            file_info = {"type": "video", "file_id": message.video.file_id}

        if file_info:
            COLLECTION.update_one(
                {"_id": main_post["_id"]},
                {"$push": {"files": file_info}}
            )

# Función de búsqueda
def search(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("🔍 Usa: /search <hashtag>")
        return

    hashtag = context.args[0].lower().strip('#')
    results = COLLECTION.find({"hashtags": hashtag})

    if not results.count():
        update.message.reply_text("❌ No hay resultados.")
        return

    for post in results:
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=post["cover"],
            caption=post["synopsis"]
        )
        for file in post["files"]:
            if file["type"] == "document":
                context.bot.send_document(update.effective_chat.id, file["file_id"])
            elif file["type"] == "video":
                context.bot.send_video(update.effective_chat.id, file["file_id"])

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("search", search, pass_args=True))
    dp.add_handler(MessageHandler(Filters.update.channel_post, save_post))

    # Webhook sin Flask
    WEBHOOK_URL = "https://nombre-de-tu-servicio.onrender.com/" + TOKEN
    updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL,
        allowed_updates=Update.ALL_TYPES
    )
    updater.idle()

if __name__ == "__main__":
    main()
