import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# توکن ربات
TOKEN = '8169710376:AAGyx3swmW-30cAuttDLuWLY-Atqbf9tURs'

# ادمین‌ها (بدون @ و حروف کوچک)
ADMINS = ['alzdelrs', 'taeed24']

# فایل چنل‌ها
CHANNELS_FILE = 'channels.json'

# بارگذاری چنل‌ها از فایل (اگر وجود نداشت، خالی بساز)
try:
    with open(CHANNELS_FILE, 'r') as f:
        CHANNELS = json.load(f)
except:
    CHANNELS = []

# فایل دیتا برای موزیک‌ها
try:
    with open('data.json', 'r') as f:
        MUSIC_DATA = json.load(f)
except:
    MUSIC_DATA = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username.lower() if user.username else None

    if not username:
        await update.message.reply_text("برای استفاده از ربات باید یک آیدی عمومی (username) داشته باشید.")
        return

    if username in ADMINS:
        await update.message.reply_text("سلام ادمین عزیز 🎧 می‌تونی موزیک آپلود کنی یا چنل اضافه/حذف کنی.")
        return

    # ساخت دکمه‌های چنل
    buttons = []
    for ch in CHANNELS:
        text = ch.replace('@', 'چنل ')
        url = f"https://t.me/{ch.replace('@','')}" if ch.startswith('@') else ch
        buttons.append([InlineKeyboardButton(text=text, url=url)])

    # دکمه عضو شدم
    buttons.append([InlineKeyboardButton("✅ عضو شدم", callback_data="check_membership")])

    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("سلام! لطفاً اول در چنل‌های زیر عضو شو 👇", reply_markup=keyboard)

async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    not_member = []
    for ch in CHANNELS:
        if ch.startswith('@'):
            try:
                member = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
                if member.status in ['left', 'kicked']:
                    not_member.append(ch)
            except:
                not_member.append(ch)

    if not_member:
        await query.edit_message_text("⛔ لطفاً ابتدا در چنل‌های زیر عضو شوید:\n" + "\n".join(not_member))
        return

    await query.edit_message_text("✅ عضویت شما تایید شد! حالا می‌تونید موزیک رو دریافت کنید.")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    if not username or username.lower() not in ADMINS:
        await update.message.reply_text("🚫 فقط ادمین‌ها می‌تونن موزیک آپلود کنن.")
        return

    file = await update.message.audio.get_file()
    file_id = file.file_id
    MUSIC_DATA[file_id] = {"title": update.message.audio.title or "بدون نام"}

    # ذخیره در فایل
    with open('data.json', 'w') as f:
        json.dump(MUSIC_DATA, f)

    await update.message.reply_text(
        f"✅ موزیک آپلود شد!\n📎 لینک مخصوص کاربران:\nhttps://t.me/{context.bot.username}?start=play_{file_id}"
    )

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 1 or not args[0].startswith('play_'):
        await update.message.reply_text("دستور نامعتبر است.")
        return

    file_id = args[0].split('_')[1]
    if file_id in MUSIC_DATA:
        await update.message.reply_audio(audio=file_id)
    else:
        await update.message.reply_text("فایل پیدا نشد یا حذف شده است.")

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    if not username or username.lower() not in ADMINS:
        await update.message.reply_text("🚫 فقط ادمین می‌تونه چنل اضافه کنه.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("📌 استفاده درست: /addchannel @channel_username یا لینک چنل")
        return

    new_ch = context.args[0]
    if new_ch not in CHANNELS:
        CHANNELS.append(new_ch)
        with open(CHANNELS_FILE, 'w') as f:
            json.dump(CHANNELS, f)
        await update.message.reply_text("✅ چنل با موفقیت اضافه شد.")
    else:
        await update.message.reply_text("⚠️ این چنل قبلاً اضافه شده است.")

async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    if not username or username.lower() not in ADMINS:
        await update.message.reply_text("🚫 فقط ادمین می‌تونه چنل حذف کنه.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("📌 استفاده درست: /removechannel @channel_username یا لینک چنل")
        return

    ch = context.args[0]
    if ch in CHANNELS:
        CHANNELS.remove(ch)
        with open(CHANNELS_FILE, 'w') as f:
            json.dump(CHANNELS, f)
        await update.message.reply_text("✅ چنل حذف شد.")
    else:
        await update.message.reply_text("⚠️ این چنل در لیست وجود ندارد.")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"👤 Username: {user.username}\n🆔 User ID: {user.id}")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_membership, pattern="check_membership"))
    app.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("addchannel", add_channel))
    app.add_handler(CommandHandler("removechannel", remove_channel))
    app.add_handler(CommandHandler("get_id", get_id))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
