import threading, re, json, os
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8443404814:AAHMhzPkOrwnJztT1suTP4Tfma_yAWVUcKY"

# ذخیره داده‌ها در حافظه
warnings = {}      # {chat_id: {user_id: count}}
bad_words = {}     # {chat_id: [word1, word2]}
locks = {}         # {chat_id: {lock_name: bool}}
lang = {}          # {chat_id: "fa" or "en"}
welcome_msg = {}   # {chat_id: "message"}

TEXTS = {
    "fa": {
        "start": "🌹 سلام {name} عزیز!\nبا بهترین ربات مدیریت گروه آشنا شوید\n\n✅ پاسخدهی سریع\n✅ فیلتر پیشرفته\n✅ کنترل دقیق دسترسی\n✅ سیستم قفل حرفه‌ای",
        "main_menu": "📚 راهنمای ربات صفحه اصلی :",
        "installed": "📗 ربات با موفقیت در گروه نصب شد\n\n➕ مالک گروه:\n▸ {owner}\n\n🔧 بطور پیشفرض قفل‌های زیر فعال شد :\n✅ قفل لینک\n✅ قفل فایل\n✅ قفل سرویس تلگرام\n✅ قفل ورود ربات\n✅ قفل تبچی\n✅ خوش‌آمدگویی",
        "banned": "🚫 {name} بن شد",
        "unbanned": "✅ {name} آنبن شد",
        "kicked": "👢 {name} کیک شد",
        "muted": "🔇 {name} سکوت شد",
        "unmuted": "🔊 {name} آنسکوت شد",
        "muted_temp": "🔇 {name} برای {time} سکوت شد",
        "promoted": "⭐ {name} ادمین شد",
        "demoted": "⬇️ {name} عزل شد",
        "warned": "⚠️ {name} اخطار گرفت! ({count}/3)\nدفعه بعد بن میشی",
        "warn_banned": "🚫 {name} بخاطر 3 اخطار بن شد",
        "no_reply": "❌ روی پیام کسی reply کن",
        "not_admin": "❌ فقط ادمین‌ها میتونن استفاده کنن",
        "lock_on": "🔒 قفل {lock} فعال شد",
        "lock_off": "🔓 قفل {lock} غیرفعال شد",
        "welcome_set": "✅ پیام خوش‌آمدگویی تنظیم شد",
        "filter_added": "✅ کلمه فیلتر اضافه شد",
        "filter_removed": "✅ کلمه فیلتر حذف شد",
        "choose_lang": "🇮🇷 زبان را انتخاب کنید :\n🇺🇸 Choose your language :",
    },
    "en": {
        "start": "🌹 Hello {name}!\nWelcome to the best group management bot\n\n✅ Fast response\n✅ Advanced filter\n✅ Precise access control\n✅ Professional lock system",
        "main_menu": "📚 Bot Guide - Main Page :",
        "installed": "📗 Bot successfully installed\n\n➕ Group Owner:\n▸ {owner}\n\n🔧 Default locks activated :\n✅ Link lock\n✅ File lock\n✅ Telegram service lock\n✅ Bot entry lock\n✅ Sticker lock\n✅ Welcome message",
        "banned": "🚫 {name} was banned",
        "unbanned": "✅ {name} was unbanned",
        "kicked": "👢 {name} was kicked",
        "muted": "🔇 {name} was muted",
        "unmuted": "🔊 {name} was unmuted",
        "muted_temp": "🔇 {name} muted for {time}",
        "promoted": "⭐ {name} promoted to admin",
        "demoted": "⬇️ {name} was demoted",
        "warned": "⚠️ {name} warned! ({count}/3)\nNext time you'll be banned",
        "warn_banned": "🚫 {name} banned for 3 warnings",
        "no_reply": "❌ Reply to a message first",
        "not_admin": "❌ Only admins can use this",
        "lock_on": "🔒 {lock} lock activated",
        "lock_off": "🔓 {lock} lock deactivated",
        "welcome_set": "✅ Welcome message set",
        "filter_added": "✅ Filter word added",
        "filter_removed": "✅ Filter word removed",
        "choose_lang": "🇮🇷 زبان را انتخاب کنید :\n🇺🇸 Choose your language :",
    }
}

def t(chat_id, key, **kwargs):
    l = lang.get(chat_id, "fa")
    text = TEXTS[l].get(key, key)
    return text.format(**kwargs)

def get_lang(chat_id):
    return lang.get(chat_id, "fa")

# HTTP server برای Render
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

async def is_admin(context, chat_id, user_id):
    try:
        m = await context.bot.get_chat_member(chat_id, user_id)
        return m.status in ["administrator", "creator"]
    except:
        return False

async def is_owner(context, chat_id, user_id):
    try:
        m = await context.bot.get_chat_member(chat_id, user_id)
        return m.status == "creator"
    except:
        return False

def main_menu_keyboard(chat_id):
    l = get_lang(chat_id)
    if l == "fa":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔒 مدیریت قفل‌ها", callback_data="menu_locks")],
            [InlineKeyboardButton("🎭 تبچی‌ها", callback_data="menu_stickers"),
             InlineKeyboardButton("⚙️ تنظیمی", callback_data="menu_settings")],
            [InlineKeyboardButton("⚖️ مجازات کاربران", callback_data="menu_punish"),
             InlineKeyboardButton("👤 پنل کاربر", callback_data="menu_user")],
            [InlineKeyboardButton("👑 ارتقا و عزل", callback_data="menu_promote")],
            [InlineKeyboardButton("🧹 پاکسازی", callback_data="menu_clean"),
             InlineKeyboardButton("🔤 فیلتر کلمات", callback_data="menu_filter")],
            [InlineKeyboardButton("👋 خوش‌آمدگویی", callback_data="menu_welcome"),
             InlineKeyboardButton("📊 آمار", callback_data="menu_stats")],
            [InlineKeyboardButton("🌐 زبان", callback_data="menu_lang")],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔒 Lock Management", callback_data="menu_locks")],
            [InlineKeyboardButton("🎭 Stickers", callback_data="menu_stickers"),
             InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")],
            [InlineKeyboardButton("⚖️ Punishments", callback_data="menu_punish"),
             InlineKeyboardButton("👤 User Panel", callback_data="menu_user")],
            [InlineKeyboardButton("👑 Promote/Demote", callback_data="menu_promote")],
            [InlineKeyboardButton("🧹 Clean", callback_data="menu_clean"),
             InlineKeyboardButton("🔤 Word Filter", callback_data="menu_filter")],
            [InlineKeyboardButton("👋 Welcome", callback_data="menu_welcome"),
             InlineKeyboardButton("📊 Stats", callback_data="menu_stats")],
            [InlineKeyboardButton("🌐 Language", callback_data="menu_lang")],
        ])

def locks_keyboard(chat_id):
    cl = locks.get(chat_id, {})
    def ico(k): return "✅" if cl.get(k) else "❌"
    l = get_lang(chat_id)
    if l == "fa":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{ico('link')} قفل لینک", callback_data="lock_link")],
            [InlineKeyboardButton(f"{ico('file')} قفل فایل", callback_data="lock_file"),
             InlineKeyboardButton(f"{ico('photo')} قفل عکس", callback_data="lock_photo")],
            [InlineKeyboardButton(f"{ico('video')} قفل ویدیو", callback_data="lock_video"),
             InlineKeyboardButton(f"{ico('sticker')} قفل استیکر", callback_data="lock_sticker")],
            [InlineKeyboardButton(f"{ico('gif')} قفل گیف", callback_data="lock_gif"),
             InlineKeyboardButton(f"{ico('forward')} قفل فوروارد", callback_data="lock_forward")],
            [InlineKeyboardButton(f"{ico('bot')} قفل ربات", callback_data="lock_bot"),
             InlineKeyboardButton(f"{ico('game')} قفل بازی", callback_data="lock_game")],
            [InlineKeyboardButton("🔒 قفل همه", callback_data="lock_all"),
             InlineKeyboardButton("🔓 باز همه", callback_data="unlock_all")],
            [InlineKeyboardButton("🔙 برگشت", callback_data="menu_main")],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{ico('link')} Link Lock", callback_data="lock_link")],
            [InlineKeyboardButton(f"{ico('file')} File Lock", callback_data="lock_file"),
             InlineKeyboardButton(f"{ico('photo')} Photo Lock", callback_data="lock_photo")],
            [InlineKeyboardButton(f"{ico('video')} Video Lock", callback_data="lock_video"),
             InlineKeyboardButton(f"{ico('sticker')} Sticker Lock", callback_data="lock_sticker")],
            [InlineKeyboardButton(f"{ico('gif')} GIF Lock", callback_data="lock_gif"),
             InlineKeyboardButton(f"{ico('forward')} Forward Lock", callback_data="lock_forward")],
            [InlineKeyboardButton(f"{ico('bot')} Bot Lock", callback_data="lock_bot"),
             InlineKeyboardButton(f"{ico('game')} Game Lock", callback_data="lock_game")],
            [InlineKeyboardButton("🔒 Lock All", callback_data="lock_all"),
             InlineKeyboardButton("🔓 Unlock All", callback_data="unlock_all")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu_main")],
        ])

def punish_keyboard(chat_id):
    l = get_lang(chat_id)
    if l == "fa":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🚫 بن", callback_data="p_ban"),
             InlineKeyboardButton("✅ آنبن", callback_data="p_unban")],
            [InlineKeyboardButton("👢 کیک", callback_data="p_kick"),
             InlineKeyboardButton("⚠️ اخطار", callback_data="p_warn")],
            [InlineKeyboardButton("🔇 سکوت", callback_data="p_mute"),
             InlineKeyboardButton("🔊 آنسکوت", callback_data="p_unmute")],
            [InlineKeyboardButton("⏱ سکوت موقت", callback_data="p_tmute")],
            [InlineKeyboardButton("🔙 برگشت", callback_data="menu_main")],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🚫 Ban", callback_data="p_ban"),
             InlineKeyboardButton("✅ Unban", callback_data="p_unban")],
            [InlineKeyboardButton("👢 Kick", callback_data="p_kick"),
             InlineKeyboardButton("⚠️ Warn", callback_data="p_warn")],
            [InlineKeyboardButton("🔇 Mute", callback_data="p_mute"),
             InlineKeyboardButton("🔊 Unmute", callback_data="p_unmute")],
            [InlineKeyboardButton("⏱ Temp Mute", callback_data="p_tmute")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu_main")],
        ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    name = user.first_name
    text = t(chat_id, "start", name=name)
    await update.message.reply_text(text, reply_markup=main_menu_keyboard(chat_id))

async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    chat_id = chat.id
    
    # پیدا کردن مالک
    owner_name = "نامشخص"
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        for a in admins:
            if a.status == "creator":
                owner_name = f"@{a.user.username}" if a.user.username else a.user.first_name
    except:
        pass
    
    # قفل‌های پیشفرض
    locks[chat_id] = {
        "link": True, "file": True, "sticker": True,
        "bot": True, "forward": False, "photo": False,
        "video": False, "gif": False, "game": False
    }
    
    text = t(chat_id, "installed", owner=owner_name)
    await update.message.reply_text(text)

async def welcome_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    for member in update.message.new_chat_members:
        if member.is_bot:
            await bot_added(update, context)
            return
        msg = welcome_msg.get(chat_id, f"👋 خوش اومدی {member.first_name}! 🌹")
        msg = msg.replace("{name}", member.first_name)
        await update.message.reply_text(msg)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    data = query.data

    if not await is_admin(context, chat_id, user_id):
        await query.answer("❌ فقط ادمین‌ها", show_alert=True)
        return

    if data == "menu_main":
        await query.edit_message_text(t(chat_id, "main_menu"), reply_markup=main_menu_keyboard(chat_id))
    
    elif data == "menu_locks":
        l = get_lang(chat_id)
        txt = "🔒 مدیریت قفل‌ها:" if l == "fa" else "🔒 Lock Management:"
        await query.edit_message_text(txt, reply_markup=locks_keyboard(chat_id))
    
    elif data == "menu_punish":
        l = get_lang(chat_id)
        txt = "⚖️ مجازات کاربران:" if l == "fa" else "⚖️ Punishments:"
        await query.edit_message_text(txt, reply_markup=punish_keyboard(chat_id))
    
    elif data == "menu_lang":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇮🇷 فارسی", callback_data="setlang_fa")],
            [InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en")],
            [InlineKeyboardButton("🔙 برگشت / Back", callback_data="menu_main")],
        ])
        await query.edit_message_text(t(chat_id, "choose_lang"), reply_markup=keyboard)
    
    elif data.startswith("setlang_"):
        lang[chat_id] = data.split("_")[1]
        await query.edit_message_text(t(chat_id, "main_menu"), reply_markup=main_menu_keyboard(chat_id))
    
    elif data.startswith("lock_") or data.startswith("unlock_"):
        if data == "lock_all":
            locks[chat_id] = {k: True for k in ["link","file","photo","video","sticker","gif","forward","bot","game"]}
        elif data == "unlock_all":
            locks[chat_id] = {k: False for k in ["link","file","photo","video","sticker","gif","forward","bot","game"]}
        else:
            lock_name = data.replace("lock_", "").replace("unlock_", "")
            if chat_id not in locks:
                locks[chat_id] = {}
            locks[chat_id][lock_name] = not locks[chat_id].get(lock_name, False)
        
        l = get_lang(chat_id)
        txt = "🔒 مدیریت قفل‌ها:" if l == "fa" else "🔒 Lock Management:"
        await query.edit_message_text(txt, reply_markup=locks_keyboard(chat_id))
    
    elif data == "menu_welcome":
        l = get_lang(chat_id)
        cur = welcome_msg.get(chat_id, "")
        if l == "fa":
            txt = f"👋 پیام خوش‌آمدگویی فعلی:\n{cur}\n\nبرای تغییر بنویس:\nخوش‌آمد [پیام جدید]"
        else:
            txt = f"👋 Current welcome:\n{cur}\n\nTo change write:\nwelcome [new message]"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 برگشت", callback_data="menu_main")]])
        await query.edit_message_text(txt, reply_markup=keyboard)
    
    elif data == "menu_filter":
        l = get_lang(chat_id)
        words = bad_words.get(chat_id, [])
        words_text = "، ".join(words) if words else ("هیچ" if l == "fa" else "None")
        if l == "fa":
            txt = f"🔤 کلمات فیلتر شده:\n{words_text}\n\nبرای افزودن: فیلتر [کلمه]\nبرای حذف: حذف‌فیلتر [کلمه]"
        else:
            txt = f"🔤 Filtered words:\n{words_text}\n\nTo add: filter [word]\nTo remove: removefilter [word]"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 برگشت", callback_data="menu_main")]])
        await query.edit_message_text(txt, reply_markup=keyboard)
    
    elif data == "menu_stats":
        try:
            count = await context.bot.get_chat_member_count(chat_id)
            l = get_lang(chat_id)
            if l == "fa":
                txt = f"📊 آمار گروه:\n👥 اعضا: {count}"
            else:
                txt = f"📊 Group Stats:\n👥 Members: {count}"
        except:
            txt = "📊 Stats unavailable"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 برگشت", callback_data="menu_main")]])
        await query.edit_message_text(txt, reply_markup=keyboard)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    msg = update.message
    text = msg.text.strip()
    text_lower = text.lower()
    chat_id = msg.chat_id
    user_id = msg.from_user.id

    # بررسی فیلتر کلمات
    words = bad_words.get(chat_id, [])
    for word in words:
        if word.lower() in text_lower:
            try:
                await msg.delete()
            except:
                pass
            return

    # بررسی قفل‌ها
    cl = locks.get(chat_id, {})
    if cl.get("link") and re.search(r'(https?://|t\.me/|@\w+)', text):
        if not await is_admin(context, chat_id, user_id):
            try: await msg.delete()
            except: pass
            return

    # دستورات ریپلی
    admin_commands_fa = ["بن", "آنبن", "کیک", "سکوت", "آنسکوت", "ادمین", "عزل", "اخطار", "حذف‌اخطار"]
    admin_commands_en = ["ban", "unban", "kick", "mute", "unmute", "admin", "demote", "warn", "unwarn"]
    
    is_cmd = text_lower in [c.lower() for c in admin_commands_fa + admin_commands_en] or \
             any(text_lower.startswith(c.lower()) for c in ["سکوت موقت", "tmute", "خوش‌آمد", "welcome", "فیلتر", "filter", "حذف‌فیلتر", "removefilter", "قفل", "lock", "آنلاک", "unlock"])
    
    if not is_cmd:
        return

    if not await is_admin(context, chat_id, user_id):
        return

    # دستورات بدون ریپلی
    if text_lower.startswith("خوش‌آمد ") or text_lower.startswith("welcome "):
        new_msg = text.split(" ", 1)[1] if " " in text else ""
        if new_msg:
            welcome_msg[chat_id] = new_msg
            await msg.reply_text(t(chat_id, "welcome_set"))
        return

    if text_lower.startswith("فیلتر ") or text_lower.startswith("filter "):
        word = text.split(" ", 1)[1] if " " in text else ""
        if word:
            if chat_id not in bad_words:
                bad_words[chat_id] = []
            bad_words[chat_id].append(word.lower())
            await msg.reply_text(t(chat_id, "filter_added"))
        return

    if text_lower.startswith("حذف‌فیلتر ") or text_lower.startswith("removefilter "):
        word = text.split(" ", 1)[1] if " " in text else ""
        if word and chat_id in bad_words and word.lower() in bad_words[chat_id]:
            bad_words[chat_id].remove(word.lower())
            await msg.reply_text(t(chat_id, "filter_removed"))
        return

    if text_lower.startswith("قفل ") or text_lower.startswith("lock "):
        lock_name = text.split(" ", 1)[1].strip() if " " in text else ""
        lock_map = {"لینک": "link", "فایل": "file", "عکس": "photo", "ویدیو": "video",
                    "استیکر": "sticker", "گیف": "gif", "فوروارد": "forward", "ربات": "bot",
                    "link": "link", "file": "file", "photo": "photo", "video": "video",
                    "sticker": "sticker", "gif": "gif", "forward": "forward", "bot": "bot"}
        if lock_name.lower() in lock_map:
            k = lock_map[lock_name.lower()]
            if chat_id not in locks:
                locks[chat_id] = {}
            locks[chat_id][k] = True
            await msg.reply_text(t(chat_id, "lock_on", lock=lock_name))
        return

    if text_lower.startswith("آنلاک ") or text_lower.startswith("unlock "):
        lock_name = text.split(" ", 1)[1].strip() if " " in text else ""
        lock_map = {"لینک": "link", "فایل": "file", "عکس": "photo", "ویدیو": "video",
                    "استیکر": "sticker", "گیف": "gif", "فوروارد": "forward", "ربات": "bot",
                    "link": "link", "file": "file", "photo": "photo", "video": "video",
                    "sticker": "sticker", "gif": "gif", "forward": "forward", "bot": "bot"}
        if lock_name.lower() in lock_map:
            k = lock_map[lock_name.lower()]
            if chat_id not in locks:
                locks[chat_id] = {}
            locks[chat_id][k] = False
            await msg.reply_text(t(chat_id, "lock_off", lock=lock_name))
        return

    # دستورات با ریپلی
    if not msg.reply_to_message:
        await msg.reply_text(t(chat_id, "no_reply"))
        return

    target = msg.reply_to_message.from_user
    target_id = target.id
    name = target.first_name

    if text_lower in ["بن", "ban"]:
        await context.bot.ban_chat_member(chat_id, target_id)
        await msg.reply_text(t(chat_id, "banned", name=name))

    elif text_lower in ["آنبن", "unban"]:
        await context.bot.unban_chat_member(ch
