cat > /home/claude/bot.py << 'ENDOFFILE'
import threading, re
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8443404814:AAHMhzPkOrwnJztT1suTP4Tfma_yAWVUcKY"

# ذخیره داده‌ها
warnings = {}
group_settings = {}
group_lang = {}
bad_words_list = {}

# ==================== وب سرور ====================
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

# ==================== توابع کمکی ====================
def get_lang(chat_id):
    return group_lang.get(chat_id, "fa")

def t(chat_id, fa, en):
    return fa if get_lang(chat_id) == "fa" else en

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

def get_settings(chat_id):
    if chat_id not in group_settings:
        group_settings[chat_id] = {
            "lock_link": True,
            "lock_file": True,
            "lock_sticker": True,
            "lock_gif": True,
            "lock_voice": True,
            "lock_video": True,
            "lock_bot": True,
            "lock_forward": False,
            "welcome": True,
            "welcome_text": None,
            "bad_words": True,
        }
    return group_settings[chat_id]

# ==================== منوها ====================
def main_menu_keyboard(chat_id):
    lang = get_lang(chat_id)
    if lang == "fa":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔒 مدیریت قفل‌ها", callback_data="menu_locks")],
            [InlineKeyboardButton("⚖️ مجازات کاربران", callback_data="menu_punish"),
             InlineKeyboardButton("👤 پنل کاربر", callback_data="menu_user")],
            [InlineKeyboardButton("👑 ارتقا و عزل", callback_data="menu_promote"),
             InlineKeyboardButton("🧹 پاکسازی", callback_data="menu_clean")],
            [InlineKeyboardButton("🔤 فیلتر کلمات", callback_data="menu_filter"),
             InlineKeyboardButton("👋 خوش‌آمدگویی", callback_data="menu_welcome")],
            [InlineKeyboardButton("📊 آمار گروه", callback_data="menu_stats"),
             InlineKeyboardButton("⚙️ تنظیمات", callback_data="menu_settings")],
            [InlineKeyboardButton("🌐 زبان", callback_data="menu_lang")],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔒 Lock Management", callback_data="menu_locks")],
            [InlineKeyboardButton("⚖️ Punishments", callback_data="menu_punish"),
             InlineKeyboardButton("👤 User Panel", callback_data="menu_user")],
            [InlineKeyboardButton("👑 Promote/Demote", callback_data="menu_promote"),
             InlineKeyboardButton("🧹 Clean", callback_data="menu_clean")],
            [InlineKeyboardButton("🔤 Word Filter", callback_data="menu_filter"),
             InlineKeyboardButton("👋 Welcome", callback_data="menu_welcome")],
            [InlineKeyboardButton("📊 Stats", callback_data="menu_stats"),
             InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")],
            [InlineKeyboardButton("🌐 Language", callback_data="menu_lang")],
        ])

def locks_keyboard(chat_id):
    s = get_settings(chat_id)
    def status(key):
        return "✅" if s.get(key) else "❌"
    lang = get_lang(chat_id)
    if lang == "fa":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{status('lock_link')} قفل لینک", callback_data="toggle_lock_link"),
             InlineKeyboardButton(f"{status('lock_file')} قفل فایل", callback_data="toggle_lock_file")],
            [InlineKeyboardButton(f"{status('lock_sticker')} قفل استیکر", callback_data="toggle_lock_sticker"),
             InlineKeyboardButton(f"{status('lock_gif')} قفل گیف", callback_data="toggle_lock_gif")],
            [InlineKeyboardButton(f"{status('lock_voice')} قفل ویس", callback_data="toggle_lock_voice"),
             InlineKeyboardButton(f"{status('lock_video')} قفل ویدیو", callback_data="toggle_lock_video")],
            [InlineKeyboardButton(f"{status('lock_bot')} قفل ربات", callback_data="toggle_lock_bot"),
             InlineKeyboardButton(f"{status('lock_forward')} قفل فوروارد", callback_data="toggle_lock_forward")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{status('lock_link')} Link", callback_data="toggle_lock_link"),
             InlineKeyboardButton(f"{status('lock_file')} File", callback_data="toggle_lock_file")],
            [InlineKeyboardButton(f"{status('lock_sticker')} Sticker", callback_data="toggle_lock_sticker"),
             InlineKeyboardButton(f"{status('lock_gif')} GIF", callback_data="toggle_lock_gif")],
            [InlineKeyboardButton(f"{status('lock_voice')} Voice", callback_data="toggle_lock_voice"),
             InlineKeyboardButton(f"{status('lock_video')} Video", callback_data="toggle_lock_video")],
            [InlineKeyboardButton(f"{status('lock_bot')} Bot", callback_data="toggle_lock_bot"),
             InlineKeyboardButton(f"{status('lock_forward')} Forward", callback_data="toggle_lock_forward")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_main")],
        ])

def punish_keyboard(chat_id):
    lang = get_lang(chat_id)
    if lang == "fa":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🚫 بن", callback_data="help_ban"),
             InlineKeyboardButton("✅ آنبن", callback_data="help_unban")],
            [InlineKeyboardButton("🔇 سکوت", callback_data="help_mute"),
             InlineKeyboardButton("🔊 آنسکوت", callback_data="help_unmute")],
            [InlineKeyboardButton("⏱ سکوت موقت", callback_data="help_tmute"),
             InlineKeyboardButton("👢 کیک", callback_data="help_kick")],
            [InlineKeyboardButton("⚠️ اخطار", callback_data="help_warn"),
             InlineKeyboardButton("🗑 حذف اخطار", callback_data="help_unwarn")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🚫 Ban", callback_data="help_ban"),
             InlineKeyboardButton("✅ Unban", callback_data="help_unban")],
            [InlineKeyboardButton("🔇 Mute", callback_data="help_mute"),
             InlineKeyboardButton("🔊 Unmute", callback_data="help_unmute")],
            [InlineKeyboardButton("⏱ Temp Mute", callback_data="help_tmute"),
             InlineKeyboardButton("👢 Kick", callback_data="help_kick")],
            [InlineKeyboardButton("⚠️ Warn", callback_data="help_warn"),
             InlineKeyboardButton("🗑 Unwarn", callback_data="help_unwarn")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_main")],
        ])

def lang_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇮🇷 فارسی", callback_data="set_lang_fa"),
         InlineKeyboardButton("🇺🇸 English", callback_data="set_lang_en")],
    ])

# ==================== استارت ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    lang = get_lang(chat_id)

    if lang == "fa":
        text = (
            f"🌹 سلام {user.first_name} عزیز\n"
            f"📗 با بهترین ربات مدیریت گروه آشنا شوید\n"
            f"📗 دستیار قدرتمند برای نظم و امنیت گروه‌ها\n"
            f"📗 حرفه‌ای‌ترین ابزار کنترل در دست شماست\n\n"
            f"✅ پاسخدهی سریع به دستورات\n"
            f"✅ فیلتر پیشرفته کلمات\n"
            f"✅ سیستم قفل و محدودیت حرفه‌ای\n"
            f"✅ مجازات کاربران\n"
            f"✅ آمار فعالیت‌ها\n\n"
            f"📚 راهنمای ربات صفحه اصلی :"
        )
    else:
        text = (
            f"🌹 Hello {user.first_name}\n"
            f"📗 Welcome to the best group management bot\n\n"
            f"✅ Fast response\n"
            f"✅ Advanced word filter\n"
            f"✅ Professional lock system\n"
            f"✅ User punishments\n"
            f"✅ Activity stats\n\n"
            f"📚 Main Menu :"
        )

    await update.message.reply_text(text, reply_markup=main_menu_keyboard(chat_id))

# ==================== وقتی ربات به گروه اضافه میشه ====================
async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    chat_id = chat.id

    # پیدا کردن مالک
    owner_name = "ناشناس"
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        for admin in admins:
            if admin.status == "creator":
                owner_name = f"@{admin.user.username}" if admin.user.username else admin.user.first_name
    except:
        pass

    settings = get_settings(chat_id)

    text = (
        f"📗 ربات با موفقیت در گروه نصب شد\n\n"
        f"➕ مالک گروه:\n"
        f"► {owner_name}\n\n"
        f"🔧 بطور پیشفرض قفل‌های زیر در گروه شما فعال شد :\n\n"
        f"✅ قفل لینک فعال\n"
        f"✅ قفل فایل فعال\n"
        f"✅ قفل سرویس تلگرام فعال\n"
        f"✅ قفل ورود ربات فعال\n"
        f"✅ قفل اد کننده ربات فعال\n"
        f"✅ قفل تبچی فعال\n"
        f"✅ قفل دستورات عمومی فعال\n"
        f"✅ خوش‌آمدگویی فعال\n\n"
        f"📚 برای مشاهده راهنما از دستور راهنما استفاده نمایید\n"
        f"⚙️ برای دریافت پنل تنظیمات دستور پنل را ارسال نمایید"
    )

    await update.message.reply_text(text)

# ==================== خوش‌آمدگویی ====================
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    settings = get_settings(chat_id)

    if not settings.get("welcome"):
        return

    for member in update.message.new_chat_members:
        if member.is_bot:
            if member.id == context.bot.id:
                await bot_added(update, context)
            continue

        name = member.first_name
        custom = settings.get("welcome_text")
        if custom:
            text = custom.replace("{name}", name)
        else:
            text = t(chat_id,
                f"👋 خوش اومدی {name}!\nامیدواریم وقت خوبی داشته باشی 🌹",
                f"👋 Welcome {name}!\nHope you have a great time 🌹")

        await update.message.reply_text(text)

# ==================== پردازش متن ====================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    msg = update.message
    text = msg.text.strip()
    chat_id = msg.chat_id
    user_id = msg.from_user.id
    lang = get_lang(chat_id)

    # بررسی قفل‌ها
    settings = get_settings(chat_id)
    admin = await is_admin(context, chat_id, user_id)

    if not admin:
        # قفل لینک
        if settings.get("lock_link") and re.search(r'(https?://|t\.me/|@\w+)', text):
            await msg.delete()
            await msg.reply_to_message and None or context.bot.send_message(
                chat_id, t(chat_id, f"🔒 {msg.from_user.first_name} لینک ممنوع است!", f"🔒 {msg.from_user.first_name} links are not allowed!"))
            return

        # فیلتر کلمات بد
        if settings.get("bad_words"):
            bw = bad_words_list.get(chat_id, [])
            for word in bw:
                if word.lower() in text.lower():
                    await msg.delete()
                    await context.bot.send_message(chat_id,
                        t(chat_id, f"⚠️ {msg.from_user.first_name} کلمه ممنوع!", f"⚠️ {msg.from_user.first_name} banned word!"))
                    return

    # دستورات متنی ادمین
    if not admin:
        return

    text_lower = text.lower()

    # پنل
    if text_lower in ["پنل", "panel"]:
        await msg.reply_text(
            t(chat_id, "⚙️ پنل مدیریت:", "⚙️ Management Panel:"),
            reply_markup=main_menu_keyboard(chat_id))
        return

    # راهنما
    if text_lower in ["راهنما", "help"]:
        await start(update, context)
        return

    if not msg.reply_to_message:
        # دستورات قفل بدون ریپلی
        if text_lower in ["قفل لینک", "lock link"]:
            settings["lock_link"] = not settings["lock_link"]
            status = "✅ فعال" if settings["lock_link"] else "❌ غیرفعال"
            await msg.reply_text(t(chat_id, f"🔒 قفل لینک {status} شد", f"🔒 Link lock {status}"))
        elif text_lower in ["قفل فایل", "lock file"]:
            settings["lock_file"] = not settings["lock_file"]
            status = "✅ فعال" if settings["lock_file"] else "❌ غیرفعال"
            await msg.reply_text(t(chat_id, f"🔒 قفل فایل {status} شد", f"🔒 File lock {status}"))
        elif text_lower in ["قفل استیکر", "lock sticker"]:
            settings["lock_sticker"] = not settings["lock_sticker"]
            status = "✅ فعال" if settings["lock_sticker"] else "❌ غیرفعال"
            await msg.reply_text(t(chat_id, f"🔒 قفل استیکر {status} شد", f"🔒 Sticker lock {status}"))
        return

    # دستورات با ریپلی
    target = msg.reply_to_message.from_user
    target_id = target.id
    name = target.first_name

    if text_lower in ["بن", "ban"]:
        await context.bot.ban_chat_member(chat_id, target_id)
        await msg.reply_text(t(chat_id, f"🚫 {name} بن شد", f"🚫 {name} was banned"))

    elif text_lower in ["آنبن", "unban"]:
        await context.bot.unban_chat_member(chat_id, target_id)
        await msg.reply_text(t(chat_id, f"✅ {name} آنبن شد", f"✅ {name} was unbanned"))

    elif text_lower in ["کیک", "kick"]:
        await context.bot.ban_chat_member(chat_id, target_id)
        await context.bot.unban_chat_member(chat_id, target_id)
        await msg.reply_text(t(chat_id, f"👢 {name} کیک شد", f"👢 {name} was kicked"))

    elif text_lower in ["سکوت", "mute"]:
        await context.bot.restrict_chat_member(chat_id, target_id, ChatPermissions(can_send_messages=False))
        await msg.reply_text(t(chat_id, f"🔇 {name} سکوت شد", f"🔇 {name} was muted"))

    elif text_lower in ["آنسکوت", "unmute"]:
        await context.bot.restrict_chat_member(chat_id, target_id, ChatPermissions(
            can_send_messages=True, can_send_media_messages=True,
            can_send_other_messages=True, can_add_web_page_previews=True))
        await msg.reply_text(t(chat_id, f"🔊 {name} آنسکوت شد", f"🔊 {name} was unmuted"))

    elif text_lower.startswith("سکوت ") or text_lower.startswith("tmute "):
        parts = text_lower.split()
        if len(parts) >= 2:
            time_str = parts[1]
            seconds = 0
            if time_str.endswith("m"):
                seconds = int(time_str[:-1]) * 60
            elif time_str.endswith("h"):
                seconds = int(time_str[:-1]) * 3600
            elif time_str.endswith("d"):
                seconds = int(time_str[:-1]) * 86400
            if seconds > 0:
                until = datetime.now() + timedelta(seconds=seconds)
                await context.bot.restrict_chat_member(chat_id, target_id,
                    ChatPermissions(can_send_messages=False), until_date=until)
                await msg.reply_text(t(chat_id,
                    f"🔇 {name} برای {parts[1]} سکوت شد",
                    f"🔇 {name} muted for {parts[1]}"))

    elif text_lower in ["ادمین", "admin"]:
        await context.bot.promote_chat_member(chat_id, target_id,
            can_delete_messages=True, can_restrict_members=True,
            can_pin_messages=True, can_invite_users=True)
        await msg.reply_text(t(chat_id, f"⭐ {name} ادمین شد", f"⭐ {name} is now admin"))

    elif text_lower in ["عزل", "demote"]:
        await context.bot.promote_chat_member(chat_id, target_id,
            can_delete_messages=False, can_restrict_members=False,
            can_pin_messages=False, can_invite_users=False,
            can_manage_chat=False)
        await msg.reply_text(t(chat_id, f"⬇️ {name} عزل شد", f"⬇️ {name} was demoted"))

    elif text_lower in ["اخطار", "warn"]:
        key = f"{chat_id}_{target_id}"
        warnings[key] = warnings.get(key, 0) + 1
        count = warnings[key]
        if count >= 3:
            await context.bot.ban_chat_member(chat_id, target_id)
            await msg.reply_text(t(chat_id,
                f"🚫 {name} ۳ اخطار گرفت و بن شد!",
                f"🚫 {name} got 3 warnings and was banned!"))
            warnings[key] = 0
        else:
            await msg.reply_text(t(chat_id,
                f"⚠️ {name} اخطار گرفت! ({count}/3)",
                f"⚠️ {name} warned! ({count}/3)"))

    elif text_lower in ["حذف اخطار", "unwarn"]:
        key = f"{chat_id}_{target_id}"
        warnings[key] = 0
        await msg.reply_text(t(chat_id, f"✅ اخطارهای {name} حذف شد", f"✅ {name}'s warnings cleared"))

    elif text_lower in ["پین", "pin"]:
        await context.bot.pin_chat_message(chat_id, msg.reply_to_message.message_id)
        await msg.reply_text(t(chat_id, "📌 پیام پین شد", "📌 Message pinned"))

    elif text_lower in ["حذف", "delete", "del"]:
        await msg.reply_to_message.delete()
        await msg.delete()

# ==================== پردازش استیکر ====================
async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    chat_id = msg.chat_id
    settings = get_settings(chat_id)
    admin = await is_admin(context, chat_id, msg.from_user.id)
    if not admin and settings.get("lock_sticker"):
        await msg.delete()

# ==================== پردازش فایل ====================
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    chat_id = msg.chat_id
    settings = get_settings(chat_id)
    admin = await is_admin(context, chat_id, msg.from_user.id)
    if not admin and settings.get("lock_file"):
        await msg.delete()

# ==================== پردازش گیف ====================
async def handle_gif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    chat_id = msg.chat_id
    settings = get_settings(chat_id)
    admin = await is_admin(context, chat_id, msg.from_user.id)
    if not admin and settings.get("lock_gif"):
        await msg.delete()

# ==================== کالبک دکمه‌ها ====================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    data = query.data
    lang = get_lang(chat_id)

    # منوی اصلی
    if data == "back_main":
        await query.edit_message_text(
            t(chat_id, "📚 راهنمای ربات صفحه اصلی :", "📚 Main Menu :"),
            reply_markup=main_menu_keyboard(chat_id))

    # منوی قفل‌ها
    elif data == "menu_locks":
        await query.edit_message_text(
            t(chat_id, "🔒 مدیریت قفل‌ها:", "🔒 Lock Management:"),
            reply_markup=locks_keyboard(chat_id))

    # تغییر قفل‌ها
    elif data.startswith("toggle_lock_"):
        key = data.replace("toggle_", "")
        settings = get_settings(chat_id)
        settings[key] = not settings.get(key, False)
        await query.edit_message_reply_markup(reply_markup=locks_keyboard(chat_id))

    # منوی مجازات
    elif data == "menu_punish":
        await query.edit_message_text(
            t(chat_id,
              "⚖️ مجازات کاربران\n\nبرای استفاده روی پیام کاربر reply کنید و بنویسید:\nبن | آنبن | سکوت | آنسکوت | کیک | ادمین | عزل | اخطار\nسکوت موقت: سکوت 1h 
