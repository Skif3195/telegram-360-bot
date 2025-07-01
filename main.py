import logging
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
import requests
from datetime import datetime
import asyncio

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
SUPABASE_TABLE = "answers"

# --- QUESTIONS ---
QUESTIONS = [
    "Оцени инициативность (1-5):",
    "Оцени коммуникабельность (1-5):",
    "Что бы ты посоветовал улучшить?"
]

# --- STATES ---
QUESTION1, QUESTION2, COMMENT = range(3)
user_responses = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Начнем оценку. Ответы анонимны.")
    await update.message.reply_text(QUESTIONS[0])
    return QUESTION1

async def q1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_responses[update.effective_chat.id] = {"initiative": update.message.text}
    await update.message.reply_text(QUESTIONS[1])
    return QUESTION2

async def q2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_responses[update.effective_chat.id]["communication"] = update.message.text
    await update.message.reply_text(QUESTIONS[2])
    return COMMENT

async def comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_responses[update.effective_chat.id]["comment"] = update.message.text
    user_responses[update.effective_chat.id]["timestamp"] = datetime.utcnow().isoformat()

    data = user_responses[update.effective_chat.id]
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json"
    }
    url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}"
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 201:
        await update.message.reply_text("Спасибо! Твои ответы сохранены анонимно.")
    else:
        await update.message.reply_text("Произошла ошибка при сохранении. Попробуй позже.")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Оценка прервана.")
    return ConversationHandler.END

# --- START TELEGRAM BOT ---
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            QUESTION1: [MessageHandler(filters.TEXT & ~filters.COMMAND, q1)],
            QUESTION2: [MessageHandler(filters.TEXT & ~filters.COMMAND, q2)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, comment)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
