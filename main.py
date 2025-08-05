from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import threading
import time
import asyncio

# חיבור ל‏Google Sheets
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPE)
client_gs = gspread.authorize(creds)
sheet = client_gs.open_by_key('1KMn38-MP3y-UYp2qkIKU4YklKq9-qihEHQ8gpQcqCB4').sheet1

# שלבים בשיחה
DATE, TIME, TOPIC, PHONE = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("שלום! לאיזו תאריך אתה רוצה לקבוע פגישה? (למשל: 10.08.2025)")
    return DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.message.text
    await update.message.reply_text("באיזו שעה? (למשל: 15:30)")
    return TIME

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['time'] = update.message.text
    await update.message.reply_text("מה נושא הפגישה?")
    return TOPIC

async def get_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['topic'] = update.message.text
    await update.message.reply_text("מה מספר הטלפון שלך?")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    user = update.message.from_user
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    # שמירה בטבלה עם טלפון וסטטוס
    sheet.append_row([
        user.full_name,
        str(user.id),
        context.user_data['date'],
        context.user_data['time'],
        context.user_data['topic'],
        context.user_data['phone'],
        now,
        'ממתין',
        ''  # הודעה ריק
    ])

    await update.message.reply_text("נרשמת בהצלחה! ניצור איתך קשר לאחר אישור הפגישה.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("הפעולה בוטלה.")
    return ConversationHandler.END

# פונקציה לבדוק אישורים בטבלה ולשלוח הודעה ללקוח
ADDRESS = "ז'בוטינסקי 85 הרצליה"

def check_confirmations(app):
    while True:
        try:
            data = sheet.get_all_records()
            for i, row in enumerate(data, start=2):
                if row['סטטוס'] == 'מאושר' and row.get('הודעה', '') != 'נשלח':
                    chat_id = int(row['מזהה טלגרם'])
                    name = row['שם לקוח']
                    message = f"{name}, הפגישה שלך אושרה! מחכים לך בזמן שנקבע 😊\nהמפגש יתקיים בכתובת: {ADDRESS}"
                    asyncio.run(app.bot.send_message(chat_id=chat_id, text=message))
                    sheet.update_cell(i, 9, 'נשלח')
                    print(f"הודעה נשלחה ל־{name}")
        except Exception as e:
            print("שגיאה בבדיקת אישורים:", e)

        time.sleep(30)

def main():
    app = ApplicationBuilder().token("7503792935:AAG8eerBwoj6_NAw1ea-569-nEFht5THhjY").build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time)],
            TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_topic)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv)

    print("📢 הבוט הופעל בהצלחה...")

    threading.Thread(target=check_confirmations, args=(app,), daemon=True).start()

    app.run_polling()

from flask import Flask
from threading import Thread

app_web = Flask('')

@app_web.route('/')
def home():
    return "I'm alive!"

def run_web():
    app_web.run(host='0.0.0.0', port=8080)

Thread(target=run_web).start()  # <<< запускается раньше

# ТОЛЬКО ПОТОМ main()
if __name__ == "__main__":
    main()

