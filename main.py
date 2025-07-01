import logging
from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import requests
from datetime import datetime

TELEGRAM_TOKEN = "7601388563:AAH2QIjzEGQaUcFIbn5TqAy9nI46HxH1uIc"
SUPABASE_URL = "https://exfvokaphpjrxsoueohj.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV4ZnZva2FwaHBqcnhzb3Vlb2hqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEzNzg2NzEsImV4cCI6MjA2Njk1NDY3MX0._8IrkMmBQPLPfcjNGW-Ecirh4kgpKwIkB5PD-_o52XA"
SUPABASE_TABLE = "answers"

logging.basicConfig(level=logging.INFO)
app = FastAPI()
tg_app = Application.builder().token(TELEGRAM_TOKEN).build()

QUESTIONS = [
    "Оцени инициативность (1-5):",
    "Оцени коммуникабельность (1-5):",
    "Что бы ты посоветовал улучшить?"
]

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

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        QUESTION1: [MessageHandler(filters.TEXT & ~filters.COMMAND, q1)],
        QUESTION2: [MessageHandler(filters.TEXT & ~filters.COMMAND, q2)],
        COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, comment)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

tg_app.add_handler(conv_handler)

@app.on_event("startup")
async def on_startup():
    tg_app.create_task(tg_app.run_polling())
