import sqlite3
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
import asyncio
import datetime
import os

TOKEN = os.getenv("TOKEN")
OWNER_ID = os.getenv("OWNER_ID")

db = sqlite3.connect("students.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS students (username TEXT, time TEXT)")
db.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Занимаюсь", callback_data="studying")],
        [InlineKeyboardButton("Курсы", callback_data="courses")]
    ]
    await update.message.reply_text("Привет, друг! Хочешь начать заниматься с PhysMath или ты уже на пути к успеху?", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    username = query.from_user.username
    if query.data == "studying":
        cursor.execute("SELECT * FROM students WHERE username=?", (f"@{username}",))
        if cursor.fetchone():
            await query.edit_message_text("Ты успешно зарегистрирован в PhysMath!")
        else:
            await query.edit_message_text("Пока тебя нет в системе. Спроси преподавателя PhysMath!")
    elif query.data == "courses":
        await query.edit_message_text("Курсы от PhysMath: Математика, Подготовка к ОГЭ, ВПР и т.д. Пиши 'math+' для записи.")

async def add_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.startswith("@"):
        parts = update.message.text.split()
        if len(parts) == 2:
            username, time_str = parts
            cursor.execute("INSERT INTO students VALUES (?, ?)", (username, time_str))
            db.commit()
            await update.message.reply_text(f"Ученик {username} добавлен на {time_str}")
        else:
            await update.message.reply_text("Формат: @username время (например, @pupil 17:00)")

async def reminders(app):
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        cursor.execute("SELECT * FROM students")
        for username, time_str in cursor.fetchall():
            reminder_time = (datetime.datetime.strptime(time_str, "%H:%M") - datetime.timedelta(minutes=10)).strftime("%H:%M")
            if now == reminder_time:
                try:
                    await app.bot.send_message(chat_id=username, text=f"Привет! У нас сегодня занятие в {time_str}")
                    await app.bot.send_message(chat_id=OWNER_ID, text=f"Напомни ученику {username} про занятие в {time_str}")
                except:
                    pass
        await asyncio.sleep(60)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_buttons))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), add_student))

async def main():
    asyncio.create_task(reminders(app))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
