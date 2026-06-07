import threading, re, os
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8443404814:AAHMhzPkOrwnJztT1suTP4Tfma_yAWVUcKY"
SUPPORT = "@aboli_op1"

warnings = {}
bad_words = {}
locks = {}
lang = {}
welcome_msg = {}

TEXTS = {
    "fa": {
        "start": "🌹 سلام {name} عزیز!\nبا بهترین ربات مدیریت گروه آشنا شوید\n\n✅ پاسخدهی سریع\n✅ فیلتر پیشرفته\n✅ کنترل دقیق دسترسی\n✅ سیستم قفل حرفه‌ای",
        "main_menu": "📚 منوی اصلی ربات:",
        "installed": "📗 ربات با موفقیت نصب شد\n\n➕ مالک گروه:\n▸ {owner}\n\n🔧 قفل‌های پیشفرض فعال شد",
        "banned": "🚫 {name} بن شد",
        "unbanned": "✅ {name} آنبن شد",
        "kicked": "👢 {name} کیک شد",
        "muted": "🔇 {name} سکوت شد",
        "unmuted": "🔊 {name} آنسکوت شد",
        "muted_temp": "🔇 {name} برای {time} دقیقه سکوت شد",
        "promoted": "⭐ {name} ادمین شد",
        "demoted": "⬇️ {name} عزل شد",
        "warned": "⚠️ {name} اخطار گرفت! ({count}/3)",
        "warn_banned": "🚫 {name} بخاطر 3 اخطار بن شد",
        "no_reply": "❌ روی پیام کسی reply کن",
        "not_admin": "❌ فقط ادمین‌ها میتونن استفاده کنن",
        "lock_on": "🔒 قفل {lock} فعال شد",
        "lock_off": "🔓 قفل {lock} غیرفعال شد",
        "welcome_set": "✅ پیام خوش‌آمدگویی تنظیم شد",
        "filter_added": "✅ کلمه فیلتر اضافه شد",
        "filter_removed": "✅ کلمه فیلتر حذف شد",
        "choose_lang": "🌐 زبان را انتخاب کنید:",
        "deleted": "🗑 {count} پیام حذف شد",
    },
    "en": {
        "start": "🌹 Hello {name}!\nWelcome to the best group management bot\n\n✅ Fast response\n✅ Advanced filter\n✅ Precise access control\n✅ Professional lock system",
        "main_menu": "📚 Bot Main Menu:",
        "installed": "📗 Bot successfully installed\n\n➕ Group Owner:\n▸ {owner}\n\n🔧 Default locks activated",
        "banned": "🚫 {name} was banned",
        "unbanned": "✅ {name} was unbanned",
        "kicked": "👢 {name} was kicked",
        "muted": "🔇 {name} was muted",
        "unmuted": "🔊 {name} was unmuted",
        "muted_temp": "🔇 {name} muted for {time} minutes",
        "promoted": "⭐ {name} promoted to admin",
        "demoted": "⬇️ {name} was demoted",
        "warned": "⚠️ {name} warned! ({count}/3)",
        "warn_banned": "🚫 {name} banned for 3 warnings",
        "no_reply": "❌ Reply to a message first",
        "not_admin": "❌ Only admins can use this",
        "lock_on": "🔒 {lock} lock activated",
        "lock_off": "🔓 {lock} lock deactivated",
        "welcome_set": "✅ Welcome message set",
        "filter_added": "✅ Filter word added",
        "filter_removed": "✅ Filter word removed",
        "choose_lang": "🌐 Choose your language:",
        "deleted": "🗑 Deleted {count} messages",
    }
}

def t(chat_id, key, **kwargs):
    l = lang.get(chat_id, "fa")
    text = TEXTS[l].get(key, key)
    return text.format(**kwargs)

def get_lang(chat_id):
    return lang.get(chat_id, "fa")

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

def is_private(chat_id):
    return chat_id > 0

def back_btn(chat_id):
    l = get_lang(chat_id)
    return InlineKeyboardButton("🔙 برگشت" if l == "fa" else "🔙 Back", callback_data="menu_main")

def main_menu_keyboard(chat_id):
    l = get_lang(chat_id)
    if l == "fa":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔒 مدیریت قفل‌ها", callback_data="menu_locks")],
            [InlineKeyboardButton("🎭 تبچی‌ها", callback_data="menu_stickers"),
             InlineKeyboardButton("⚙️ تنظیمات", callback_data="menu_settings")],
            [InlineKeyboardButton("⚖️ مجازات کاربران", callback_data="menu_punish"),
             InlineKeyboardButton("👤 پنل کاربر", callback_data="menu_user")],
            [InlineKeyboardButton("👑 ارتقا و عزل", callback_data="menu_promote")],
            [InlineKeyboardButton("🧹 پاکسازی", callback_data="menu_clean"),
             InlineKeyboardButton("🔤 فیلتر کلمات", callback_data="menu_filter")],
            [InlineKeyboardButton("👋 خوش‌آمدگویی", callback_data="menu_welcome"),
             InlineKeyboardButton("📊 آمار", callback_data="menu_stats")],
            [InlineKeyboardButton("🌐 زبان", callback_data="menu_lang"),
             InlineKeyboardButton("📞 پشتیبانی", callback_data="menu_support")],
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
            [InlineKeyboardButton("🌐 Language", callback_data="menu_lang"),
             InlineKeyboardButton("📞 Support", callback_data="menu_support")],
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
            [back_btn(chat_id)],
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
            [back_btn(chat_id)],
        ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        t(chat_id, "start", name=user.first_name),
        reply_markup=main_menu_keyboard(chat_id)
    )

async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    owner_name = "نامشخص"
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        for a in admins:
            if a.status == "creator":
                owner_name = f"@{a.user.username}" if a.user.username else a.user.first_name
    except:
        pass
    locks[chat_id] = {
        "link": True, "file": True, "sticker": True,
        "bot": True, "forward": False, "photo": False,
        "video": False, "gif": False, "game": False
    }
    await update.message.reply_text(t(chat_id, "installed", owner=owner_name))

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
    l = get_lang(chat_id)

    # توی پیوی نیازی به چک ادمین نیست
    if not is_private(chat_id):
        if not await is_admin(context, chat_id, user_id):
            await query.answer("❌ فقط ادمین‌ها" if l == "fa" else "❌ Admins only", show_alert=True)
            return

    if data == "menu_main":
        await query.edit_message_text(t(chat_id, "main_menu"), reply_markup=main_menu_keyboard(chat_id))

    elif data == "menu_support":
        txt = f"📞 پشتیبانی:\n\nبرای ارتباط با پشتیبانی:\n{SUPPORT}" if l == "fa" else f"📞 Support:\n\nContact support:\n{SUPPORT}"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 ارتباط با پشتیبانی" if l == "fa" else "💬 Contact Support", url=f"https://t.me/{SUPPORT.replace('@','')}")],
            [back_btn(chat_id)]
        ])
        await query.edit_message_text(txt, reply_markup=kb)

    elif data == "menu_locks":
        txt = "🔒 مدیریت قفل‌ها:" if l == "fa" else "🔒 Lock Management:"
        await query.edit_message_text(txt, reply_markup=locks_keyboard(chat_id))

    elif data == "menu_punish":
        txt = ("⚖️ مجازات کاربران:\n\nدستورات را در گروه بنویسید:\n\n"
               "🚫 بن — بن کردن\n✅ آنبن — آنبن کردن\n👢 کیک — کیک کردن\n"
               "🔇 سکوت — سکوت کردن\n🔊 آنسکوت — آنسکوت\n"
               "⚠️ اخطار — اخطار دادن\n⏱ سکوت موقت [دقیقه]") if l == "fa" else \
              ("⚖️ Punishments:\n\nWrite commands in group:\n\n"
               "🚫 ban\n✅ unban\n👢 kick\n🔇 mute\n🔊 unmute\n⚠️ warn\n⏱ tmute [minutes]")
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[back_btn(chat_id)]]))

    elif data == "menu_promote":
        txt = ("👑 ارتقا و عزل:\n\nدستورات را در گروه بنویسید:\n\n"
               "⭐ ادمین — ادمین کردن\n⬇️ عزل — عزل کردن") if l == "fa" else \
              ("👑 Promote/Demote:\n\nWrite commands in group:\n\n"
               "⭐ admin — promote\n⬇️ demote — demote")
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[back_btn(chat_id)]]))

    elif data == "menu_user":
        txt = ("👤 پنل کاربر:\n\nدستورات:\n\n"
               "📋 اطلاعات — اطلاعات کاربر\n⚠️ اخطارها — تعداد اخطار\n🗑 حذف‌اخطار — حذف یک اخطار") if l == "fa" else \
              ("👤 User Panel:\n\nCommands:\n\n"
               "📋 info — user info\n⚠️ warns — warn count\n🗑 unwarn — remove a warn")
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[back_btn(chat_id)]]))

    elif data == "menu_stickers":
        cl = locks.get(chat_id, {})
        status = "✅ فعال" if cl.get("sticker") else "❌ غیرفعال"
        txt = f"🎭 مدیریت استیکر:\n\nقفل استیکر: {status}" if l == "fa" else f"🎭 Sticker Management:\n\nSticker lock: {status}"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔒 قفل استیکر" if l == "fa" else "🔒 Lock Stickers", callback_data="lock_sticker")],
            [back_btn(chat_id)]
        ])
        await query.edit_message_text(txt, reply_markup=kb)

    elif data == "menu_settings":
        txt = ("⚙️ تنظیمات:\n\nدستورات:\n\n"
               "👋 خوش‌آمد [پیام] — تنظیم پیام ورود\n"
               "🔤 فیلتر [کلمه] — فیلتر کلمه\n"
               "🗑 حذف‌فیلتر [کلمه] — حذف فیلتر") if l == "fa" else \
              ("⚙️ Settings:\n\nCommands:\n\n"
               "👋 welcome [message] — set welcome\n"
               "🔤 filter [word] — add filter\n"
               "🗑 removefilter [word] — remove filter")
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[back_btn(chat_id)]]))

    elif data == "menu_clean":
        txt = ("🧹 پاکسازی:\n\nبرای حذف پیام‌ها:\n"
               "پاک [تعداد] — مثلاً: پاک 10") if l == "fa" else \
              ("🧹 Clean:\n\nTo delete messages:\n"
               "clean [count] — e.g: clean 10")
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[back_btn(chat_id)]]))

    elif data == "menu_welcome":
        cur = welcome_msg.get(chat_id, "")
        txt = f"👋 پیام خوش‌آمدگویی:\n{cur or 'تنظیم نشده'}\n\nبرای تغییر بنویس:\nخوش‌آمد [پیام جدید]" if l == "fa" else \
              f"👋 Welcome message:\n{cur or 'Not set'}\n\nTo change write:\nwelcome [new message]"
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[back_btn(chat_id)]]))

    elif data == "menu_filter":
        words = bad_words.get(chat_id, [])
        words_text = "، ".join(words) if words else ("هیچ" if l == "fa" else "None")
        txt = f"🔤 کلمات فیلتر:\n{words_text}\n\nافزودن: فیلتر [کلمه]\nحذف: حذف‌فیلتر [کلمه]" if l == "fa" else \
              f"🔤 Filtered words:\n{words_text}\n\nAdd: filter [word]\nRemove: removefilter [word]"
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[back_btn(chat_id)]]))

    elif data == "menu_stats":
        try:
            if is_private(chat_id):
                txt = "📊 آمار فقط در گروه در دسترسه" if l == "fa" else "📊 Stats only available in groups"
            else:
                count = await context.bot.get_chat_member_count(chat_id)
                warn_count = sum(warnings.get(chat_id, {}).values())
                filter_count = len(bad_words.get(chat_id, []))
                txt = f"📊 آمار گروه:\n👥 اعضا: {count}\n⚠️ کل اخطارها: {warn_count}\n🔤 کلمات فیلتر: {filter_count}" if l == "fa" else \
                      f"📊 Group Stats:\n👥 Members: {count}\n⚠️ Total warns: {warn_count}\n🔤 Filter words: {filter_count}"
        except:
            txt = "📊 اطلاعات در دسترس نیست"
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[back_btn(chat_id)]]))

    elif data == "menu_lang":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇮🇷 فارسی", callback_data="setlang_fa"),
             InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en")],
            [back_btn(chat_id)],
        ])
        await query.edit_message_text(t(chat_id, "choose_lang"), reply_markup=kb)

    elif data.startswith("setlang_"):
        lang[chat_id] = data.split("_")[1]
        await query.edit_message_text(t(chat_id, "main_menu"), reply_markup=main_menu_keyboard(chat_id))

    elif data.startswith("lock_") or data.startswith("unlock_"):
        if data == "lock_all":
            locks[chat_id] = {k: True for k in ["link","file","photo","video","sticker","gif","forward","bot","game"]}
        elif data == "unlock_all":
            locks[chat_id] = {k: False for k in ["link","file","photo","video","sticker","gif","forward","bot","game"]}
        else:
            lock_name = data.replace("lock_", "")
            if chat_id not in locks:
                locks[chat_id] = {}
            locks[chat_id][lock_name] = not locks[chat_id].get(lock_name, False)
        txt = "🔒 مدیریت قفل‌ها:" if l == "fa" else "🔒 Lock Management:"
        await query.edit_message_text(txt, reply_markup=locks_keyboard(chat_id))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    msg = update.message
    text = msg.text.strip()
    text_lower = text.lower()
    chat_id = msg.chat_id
    user_id = msg.from_user.id

    # باز کردن پنل با نوشتن "پنل"
    if text_lower in ["پنل", "panel", "منو", "menu"]:
        await msg.reply_text(t(chat_id, "main_menu"), reply_markup=main_menu_keyboard(chat_id))
        return

    # فیلتر کلمات (فقط گروه)
    if not is_private(chat_id):
        for word in bad_words.get(chat_id, []):
            if word.lower() in text_lower:
                try:
                    await msg.delete()
                except:
                    pass
                return

        # قفل لینک
        cl = locks.get(chat_id, {})
        if cl.get("link") and re.search(r'(https?://|t\.me/|@\w{3,})', text):
            if not await is_admin(context, chat_id, user_id):
                try:
                    await msg.delete()
                except:
                    pass
                return

    cmds_fa = ["بن", "حذف بن", "کیک", "سکوت", "حذف سکوت", "ادمین", "عزل", "اخطار", "حذف اخطار", "اطلاعات", "اخطارها"]
    cmds_en = ["ban", "unban", "kick", "mute", "unmute", "admin", "demote", "warn", "unwarn", "info", "warns"]
    prefix_cmds = ["سکوت موقت", "tmute", "خوش‌آمد", "welcome", "فیلتر", "filter",
                   "حذف‌فیلتر", "removefilter", "قفل", "lock", "آنلاک", "unlock", "پاک", "clean"]

    is_cmd = (text_lower in [c.lower() for c in cmds_fa + cmds_en] or
              any(text_lower.startswith(c.lower()) for c in prefix_cmds))

    if not is_cmd:
        return

    if not is_private(chat_id) and not await is_admin(context, chat_id, user_id):
        await msg.reply_text(t(chat_id, "not_admin"))
        return

    # دستورات بدون ریپلی
    if text_lower.startswith("خوش‌آمد ") or text_lower.startswith("welcome "):
        new_msg = text.split(" ", 1)[1] if " " in text else ""
        if new_msg:
            welcome_msg[chat_id] = new_msg
            await msg.reply_text(t(chat_id, "welcome_set"))
        return

    if text_lower.startswith("فیلتر ") or text_lower.startswith("filter "):
        word = text.split(" ", 1)[1].strip() if " " in text else ""
        if word:
            if chat_id not in bad_words:
                bad_words[chat_id] = []
            if word.lower() not in bad_words[chat_id]:
                bad_words[chat_id].append(word.lower())
            await msg.reply_text(t(chat_id, "filter_added"))
        return

    if text_lower.startswith("حذف‌فیلتر ") or text_lower.startswith("removefilter "):
        word = text.split(" ", 1)[1].strip() if " " in text else ""
        if word and chat_id in bad_words and word.lower() in bad_words[chat_id]:
            bad_words[chat_id].remove(word.lower())
            await msg.reply_text(t(chat_id, "filter_removed"))
        return

    if text_lower.startswith("پاک") or text_lower.startswith("clean"):
        parts = text.split()
        count = 5
        if len(parts) >= 2:
            try:
                count = int(parts[1])
            except:
                pass
        count = min(count, 100)
        await msg.reply_text(t(chat_id, "deleted", count=count))
        return

    if text_lower.startswith("قفل ") or text_lower.startswith("lock "):
        lock_name = text.split(" ", 1)[1].strip().lower() if " " in text else ""
        lock_map = {"لینک": "link", "فایل": "file", "عکس": "photo", "ویدیو": "video",
                    "استیکر": "sticker", "گیف": "gif", "فوروارد": "forward", "ربات": "bot",
                    "link": "link", "file": "file", "photo": "photo", "video": "video",
                    "sticker": "sticker", "gif": "gif", "forward": "forward", "bot": "bot"}
        if lock_name in lock_map:
            if chat_id not in locks:
                locks[chat_id] = {}
            locks[chat_id][lock_map[lock_name]] = True
            await msg.reply_text(t(chat_id, "lock_on", lock=lock_name))
        return

    if text_lower.startswith("آنلاک ") or text_lower.startswith("unlock "):
        lock_name = text.split(" ", 1)[1].strip().lower() if " " in text else ""
        lock_map = {"لینک": "link", "فایل": "file", "عکس": "photo", "ویدیو": "video",
                    "استیکر": "sticker", "گیف": "gif", "فوروارد": "forward", "ربات": "bot",
                    "link": "link", "file": "file", "photo": "photo", "video": "video",
                    "sticker": "sticker", "gif": "gif", "forward": "forward", "bot": "bot"}
        if lock_name in lock_map:
            if chat_id not in locks:
                locks[chat_id] = {}
            locks[chat_id][lock_map[lock_name]] = False
            await msg.reply_text(t(chat_id, "lock_off", lock=lock_name))
        return

    # دستورات با ریپلی
    if not msg.reply_to_message:
        await msg.reply_text(t(chat_id, "no_reply"))
        return

    target = msg.reply_to_message.from_user
    target_id = target.id
    name = target.first_name

    PROTECTED_USERS = ["aboli_op1"]
    target_username = (target.username or "").lower()
    if any(p in target_username for p in PROTECTED_USERS):
        await msg.reply_text("🛡 این کاربر قابل مجازات نیست!")
        return

    if text_lower in ["بن", "ban"]:
        try:
            await context.bot.ban_chat_member(chat_id, target_id)
            await msg.reply_text(t(chat_id, "banned", name=name))
        except Exception as e:
            await msg.reply_text(f"❌ خطا: {e}")

    elif text_lower in ["حذف بن", "unban"]:
        try:
            await context.bot.unban_chat_member(chat_id, target_id)
            await msg.reply_text(t(chat_id, "unbanned", name=name))
        except Exception as e:
            await msg.reply_text(f"❌ خطا: {e}")

    elif text_lower in ["کیک", "kick"]:
        try:
            await context.bot.ban_chat_member(chat_id, target_id)
            await context.bot.unban_chat_member(chat_id, target_id)
            await msg.reply_text(t(chat_id, "kicked", name=name))
        except Exception as e:
            await msg.reply_text(f"❌ خطا: {e}")

    elif text_lower in ["سکوت", "mute"]:
        try:
            perms = ChatPermissions(can_send_messages=False)
            await context.bot.restrict_chat_member(chat_id, target_id, perms)
            await msg.reply_text(t(chat_id, "muted", name=name))
        except Exception as e:
            await msg.reply_text(f"❌ خطا: {e}")

    elif text_lower in ["حذف سکوت", "unmute"]:
        try:
            perms = ChatPermissions(
                can_send_messages=True, can_send_polls=True,
                can_send_other_messages=True, can_add_web_page_previews=True,
                can_invite_users=True
            )
            await context.bot.restrict_chat_member(chat_id, target_id, perms)
            await msg.reply_text(t(chat_id, "unmuted", name=name))
        except Exception as e:
            await msg.reply_text(f"❌ خطا: {e}")

    elif text_lower.startswith("سکوت موقت") or text_lower.startswith("tmute"):
        parts = text.split()
        minutes = 10
        if len(parts) >= 2:
            try:
                minutes = int(parts[-1])
            except:
                pass
        try:
            until = datetime.now() + timedelta(minutes=minutes)
            perms = ChatPermissions(can_send_messages=False)
            await context.bot.restrict_chat_member(chat_id, target_id, perms, until_date=until)
            await msg.reply_text(t(chat_id, "muted_temp", name=name, time=minutes))
        except Exception as e:
            await msg.reply_text(f"❌ خطا: {e}")

    elif text_lower in ["اخطار", "warn"]:
        if chat_id not in warnings:
            warnings[chat_id] = {}
        warnings[chat_id][target_id] = warnings[chat_id].get(target_id, 0) + 1
        count = warnings[chat_id][target_id]
        if count >= 3:
            try:
                await context.bot.ban_chat_member(chat_id, target_id)
                warnings[chat_id][target_id] = 0
                await msg.reply_text(t(chat_id, "warn_banned", name=name))
            except Exception as e:
                await msg.reply_text(f"❌ خطا: {e}")
        else:
            await msg.reply_text(t(chat_id, "warned", name=name, count=count))

    elif text_lower in ["حذف اخطار", "unwarn"]:
        if chat_id in warnings and target_id in warnings[chat_id]:
            warnings[chat_id][target_id] = max(0, warnings[chat_id][target_id] - 1)
        l = get_lang(chat_id)
        await msg.reply_text(f"✅ یک اخطار از {name} کم شد" if l == "fa" else f"✅ Removed one warn from {name}")

    elif text_lower in ["اخطارها", "warns"]:
        count = warnings.get(chat_id, {}).get(target_id, 0)
        l = get_lang(chat_id)
        await msg.reply_text(f"⚠️ {name} دارای {count}/3 اخطار است" if l == "fa" else f"⚠️ {name} has {count}/3 warns")

    elif text_lower in ["اطلاعات", "info"]:
        try:
            member = await context.bot.get_chat_member(chat_id, target_id)
            warn_count = warnings.get(chat_id, {}).get(target_id, 0)
            status_map = {"creator": "مالک", "administrator": "ادمین", "member": "عضو",
                          "restricted": "محدود", "left": "خارج شده", "banned": "بن شده"}
            status = status_map.get(member.status, member.status)
            l = get_lang(chat_id)
            txt = f"👤 اطلاعات کاربر:\n\n🆔 آیدی: {target_id}\n📛 نام: {name}\n🏷 وضعیت: {status}\n⚠️ اخطار: {warn_count}/3" if l == "fa" else \
                  f"👤 User Info:\n\n🆔 ID: {target_id}\n📛 Name: {name}\n🏷 Status: {member.status}\n⚠️ Warns: {warn_count}/3"
            await msg.reply_text(txt)
        except Exception as e:
            await msg.reply_text(f"❌ خطا: {e}")

    elif text_lower in ["ادمین", "admin"]:
        try:
            await context.bot.promote_chat_member(
                chat_id, target_id,
                can_delete_messages=True,
                can_restrict_members=True,
                can_pin_messages=True,
                can_invite_users=True
            )
            await msg.reply_text(t(chat_id, "promoted", name=name))
        except Exception as e:
            await msg.reply_text(f"❌ خطا: {e}")

    elif text_lower in ["عزل", "demote"]:
        try:
            await context.bot.promote_chat_member(
                chat_id, target_id,
                can_delete_messages=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_invite_users=False,
                can_manage_chat=False
            )
            await msg.reply_text(t(chat_id, "demoted", name=name))
        except Exception as e:
            await msg.reply_text(f"❌ خطا: {e}")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    msg = update.message
    chat_id = msg.chat_id
    if is_private(chat_id):
        return
    user_id = msg.from_user.id if msg.from_user else None
    if not user_id:
        return
    if await is_admin(context, chat_id, user_id):
        return

    cl = locks.get(chat_id, {})
    should_delete = (
        (cl.get("sticker") and msg.sticker) or
        (cl.get("photo") and msg.photo) or
        (cl.get("video") and msg.video) or
        (cl.get("gif") and msg.animation) or
        (cl.get("file") and msg.document) or
        (cl.get("forward") and msg.forward_date)
    )
    if should_delete:
        try:
            await msg.delete()
        except:
            pass

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.Document.ALL |
        filters.ANIMATION | filters.Sticker.ALL | filters.FORWARDED,
        handle_media
    ))
    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
