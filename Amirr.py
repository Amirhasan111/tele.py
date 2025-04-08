import random
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackContext, filters

BOT_TOKEN = '7927215895:AAElxh2_XmrkruVoBSjIWHTEU42wKj3wxyk'
ADMIN_ID = 7101617810

bot = Bot(token=BOT_TOKEN)

user_messages = {}
user_ids = set()
blocked_users = set()  # ⛔ لیست کاربران مسدودشده
forbidden_words = []
total_messages = 0

async def start(update: Update, context: CallbackContext) -> None:
    
    user_ids.add(update.message.from_user.id)
    
    await update.message.reply_text("سلام! پیام خودتون رو وارد کنید 🌸")
    

async def forward_to_admin(update: Update, context: CallbackContext) -> None:
    global total_messages
    total_messages += 1

    if update.message:
        message = update.message

        if message.from_user.id == ADMIN_ID:
            if message.reply_to_message:
                for user_id, msg_id in user_messages.items():
                    if msg_id == message.reply_to_message.message_id:
                        await bot.send_message(chat_id=user_id, text=message.text)
                        await message.reply_text("پیام شما با موفقیت ارسال شد ✅")
                        break
            return

        if message.from_user.id in blocked_users:
            return  # ⛔ اگر کاربر مسدود شده، پیام نادیده گرفته شود

        user_ids.add(message.from_user.id)
        message_text = message.text.lower() if message.text else ""

        if any(word in message_text for word in forbidden_words):
            await message.delete()
            await message.reply_text("پیام شما حاوی کلمات فیلتر شده است و حذف شد.")
            return

       
        user_info = (
            f"آیدی عددی: {message.from_user.id}\n"
            f"آیدی کاربر: @{message.from_user.username or 'ناموجود'}"
        )

        if message.text:
            user_info += f"\nپیام کاربر: {message.text}"
            sent_message = await bot.send_message(chat_id=ADMIN_ID, text=user_info)
        elif message.photo:
            user_info += "\nکاربر یک عکس ارسال کرد."
            photo_file = message.photo[-1].file_id
            sent_message = await bot.send_photo(chat_id=ADMIN_ID, photo=photo_file, caption=user_info)
        elif message.voice:
            user_info += "\nکاربر یک ویس ارسال کرد."
            voice_file = message.voice.file_id
            sent_message = await bot.send_voice(chat_id=ADMIN_ID, voice=voice_file, caption=user_info)
        else:
            return  # اگر نوع پیام پشتیبانی نشه

        user_messages[message.from_user.id] = sent_message.message_id
        save_user_messages()
        await bot.send_message(chat_id=message.chat_id, text="پیام شما به ادمین ارسال شد، از شکیبایی شما سپاسگزارم 🌺", reply_to_message_id=message.message_id)

# 📛 دستور مسدود کردن کاربر
async def block_user(update: Update, context: CallbackContext) -> None:
    if update.message and update.message.reply_to_message:
        if update.message.from_user.id == ADMIN_ID:
            for user_id, msg_id in user_messages.items():
                if msg_id == update.message.reply_to_message.message_id:
                    blocked_users.add(user_id)
                    await update.message.reply_text(f"کاربر {user_id} با موفقیت مسدود شد ❌")
                    return
            await update.message.reply_text("کاربر مورد نظر در لیست یافت نشد.")
        else:
            await update.message.reply_text("شما اجازه استفاده از این دستور را ندارید.")
    else:
        await update.message.reply_text("لطفاً روی پیام کاربر ریپلای کنید و سپس این دستور را وارد کنید.")

        blocked_users.add(user_id)
    save_blocked_users()  # ✅ ذخیره

# دستورات فیلتر کلمات
async def add_filter(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == ADMIN_ID:
        if context.args:
            word = " ".join(context.args).lower()
            forbidden_words.append(word)
            await update.message.reply_text(f"کلمه {word} به لیست فیلتر اضافه شد.")
        else:
            await update.message.reply_text("لطفاً یک کلمه وارد کنید.")
    else:
        await update.message.reply_text("دسترسی مجاز نیست.")
        forbidden_words.append(word)
    save_filters()  # ✅ ذخیره



async def show_filters(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == ADMIN_ID:
        if forbidden_words:
            await update.message.reply_text("کلمات فیلتر شده:\n" + "\n".join(forbidden_words))
        else:
            await update.message.reply_text("هیچ کلمه‌ای فیلتر نشده است.")
    else:
        await update.message.reply_text("دسترسی مجاز نیست.")

    


async def remove_filter(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == ADMIN_ID:
        if context.args:
            word = " ".join(context.args).lower()
            if word in forbidden_words:
                forbidden_words.remove(word)
                await update.message.reply_text(f"کلمه {word} حذف شد.")
            else:
                await update.message.reply_text("کلمه مورد نظر یافت نشد.")
        else:
            await update.message.reply_text("لطفاً یک کلمه وارد کنید.")
    else:
        await update.message.reply_text("دسترسی مجاز نیست.")
    forbidden_words.remove(word)
    save_filters()  # ✅ ذخیره


async def broadcast_to_all(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == ADMIN_ID:
        msg = " ".join(context.args)
        if not msg:
            await update.message.reply_text("لطفاً یک پیام وارد کنید.")
            return
        for user_id in user_ids:
            try:
                await bot.send_message(chat_id=user_id, text=msg)
            except Exception as e:
                if "bot was blocked by the user" in str(e):
                    try:
                        user = await bot.get_chat(user_id)
                        username = f"@{user.username}" if user.username else "یوزرنیم موجود نیست"
                        await bot.send_message(
                            chat_id=ADMIN_ID,
                            text=f"😱 وای! کاربر {username} ({user_id}) ما رو مسدود کرد!"
                        )
                    except:
                        await bot.send_message(
                            chat_id=ADMIN_ID,
                            text=f"😱 وای! کاربری با آیدی ({user_id}) ما رو مسدود کرد! (یوزرنیم پیدا نشد)"
                        )
                else:
                    print(f"خطا هنگام ارسال به {user_id}: {e}")
        await update.message.reply_text("پیام به همه ارسال شد ✅")
    else:
        await update.message.reply_text("دسترسی مجاز نیست.")


import json
import os

# ذخیره کلمات فیلتر شده
def save_filters():
    with open("filters.json", "w", encoding="utf-8") as f:
        json.dump(forbidden_words, f, ensure_ascii=False)

# بارگذاری کلمات فیلتر شده
def load_filters():
    global forbidden_words
    if os.path.exists("filters.json"):
        with open("filters.json", "r", encoding="utf-8") as f:
            forbidden_words = json.load(f)

# ذخیره کاربران بلاک شده
def save_blocked_users():
    with open("blocked_users.json", "w", encoding="utf-8") as f:
        json.dump(list(blocked_users), f)

# بارگذاری کاربران بلاک شده
def load_blocked_users():
    global blocked_users
    if os.path.exists("blocked_users.json"):
        with open("blocked_users.json", "r", encoding="utf-8") as f:
            blocked_users.update(json.load(f))




def save_user_messages():
    with open("user_messages.json", "w", encoding="utf-8") as f:
        json.dump(user_messages, f)

def load_user_messages():
    global user_messages
    if os.path.exists("user_messages.json"):
        with open("user_messages.json", "r", encoding="utf-8") as f:
            user_messages = json.load(f)
            user_messages = {int(k): v for k, v in user_messages.items()}  # تبدیل کلیدها به عدد


def main():
    load_filters()
    load_blocked_users()
    load_user_messages()  # ✅ بارگذاری پیام‌های قبلی
    load_filters()
    load_blocked_users()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_to_admin))
    application.add_handler(CommandHandler("block", block_user))  # ✅ دستور بلاک
    application.add_handler(CommandHandler("addfilter", add_filter))
    application.add_handler(CommandHandler("showfilters", show_filters))
    application.add_handler(CommandHandler("removefilter", remove_filter))
    application.add_handler(CommandHandler("broadcast", broadcast_to_all))

    application.run_polling()

if __name__ == '__main__':
    main()
