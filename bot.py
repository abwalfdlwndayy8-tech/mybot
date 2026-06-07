import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ChatPermissions
from telegram.ext import Application, MessageHandler, CommandHandler, filters

TOKEN = "8443404814:AAHMhzPkOrwnJztT1suTP4Tfma_yAWVUcKY"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass

def run_server():
    HTTPServer(("0.0.0.0", 10000), Handler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

async def start(update, context):
    await update.message.reply_text("سلام! ربات فعاله\nکلمات: بن، آنبن، سکوت، آنسکوت، کیک، ادمین، عزل، اخطار")

async def handle_text(update, context):
    if not update.message or not update.message.text:
        return
    
    msg = update.message
    text = msg.text.strip().lower()
    chat_id = msg.chat_id
    
    # فقط ادمین‌ها بتونن استفاده کنن
    member = await context.bot.get_chat_member(chat_id, msg.from_user.id)
    if member.status not in ["administrator", "creator"]:
        return
    
    # باید reply باشه
    if not msg.reply_to_message:
        return
    
    target = msg.reply_to_message.from_user
    target_id = target.id
    name = target.first_name

    if text == "بن":
        await context.bot.ban_chat_member(chat_id, target_id)
        await msg.reply_text(f"🚫 {name} بن شد")

    elif text == "آنبن":
        await context.bot.unban_chat_member(chat_id, target_id)
        await msg.reply_text(f"✅ {name} آنبن شد")

    elif text == "کیک":
        await context.bot.ban_chat_member(chat_id, target_id)
        await context.bot.unban_chat_member(chat_id, target_id)
        await msg.reply_text(f"👢 {name} کیک شد")

    elif text == "سکوت":
        await context.bot.restrict_chat_member(chat_id, target_id, ChatPermissions(can_send_messages=False))
        await msg.reply_text(f"🔇 {name} سکوت شد")

    elif text == "آنسکوت":
        await context.bot.restrict_chat_member(chat_id, target_id, ChatPermissions(
            can_send_messages=True, can_send_media_messages=True,
            can_send_other_messages=True, can_add_web_page_previews=True))
        await msg.reply_text(f"🔊 {name} آنسکوت شد")

    elif text == "ادمین":
        await context.bot.promote_chat_member(chat_id, target_id,
            can_delete_messages=True, can_restrict_members=True,
            can_pin_messages=True, can_invite_users=True)
        await msg.reply_text(f"⭐ {name} ادمین شد")

    elif text == "عزل":
        await context.bot.promote_chat_member(chat_id, target_id,
            can_delete_messages=False, can_restrict_members=False,
            can_pin_messages=False, can_invite_users=False)
        await msg.reply_text(f"⬇️ {name} عزل شد")

    elif text == "اخطار":
        await msg.reply_text(f"⚠️ {name} اخطار گرفت! دفعه بعد بن میشی")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
