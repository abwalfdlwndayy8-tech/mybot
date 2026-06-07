from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8443404814:AAHMhzPkOrwnJztT1suTP4Tfma_yAWVUcKY"

async def welcome(update, context):
    for m in update.message.new_chat_members:
        await update.message.reply_text(f"Welcome {m.first_name}!")

async def ban(update, context):
    if not update.message.reply_to_message: return
    u = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, u.id)
    await update.message.reply_text(f"Banned {u.first_name}")

async def mute(update, context):
    if not update.message.reply_to_message: return
    u = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(update.effective_chat.id, u.id, ChatPermissions(can_send_messages=False))
    await update.message.reply_text(f"Muted {u.first_name}")

async def unmute(update, context):
    if not update.message.reply_to_message: return
    u = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(update.effective_chat.id, u.id, ChatPermissions(can_send_messages=True))
    await update.message.reply_text(f"Unmuted {u.first_name}")

async def kick(update, context):
    if not update.message.reply_to_message: return
    u = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, u.id)
    await context.bot.unban_chat_member(update.effective_chat.id, u.id)
    await update.message.reply_text(f"Kicked {u.first_name}")

async def rules(update, context):
    await update.message.reply_text("Rules: 1.Respect 2.No ads 3.No spam")

async def help_cmd(update, context):
    await update.message.reply_text("/ban /kick /mute /unmute /rules")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("help", help_cmd))
    app.run_polling()

if __name__ == "__main__":
    main()
