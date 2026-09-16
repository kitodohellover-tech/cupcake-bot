import os
import telebot
import requests
from flask import Flask
import threading

BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_KEY")

bot = telebot.TeleBot(BOT_TOKEN, request_timeout=30)

# Мини-веб-сервер, чтобы Render не усыплял сервис
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

dialogues = {}

@bot.message_handler(commands=['start'])
def start(message):
    dialogues[message.chat.id] = []
    bot.send_message(message.chat.id, "👋 Привет! Я CupCake. Спрашивай что угодно.")

@bot.message_handler(func=lambda m: True)
def chat(message):
    user_id = message.chat.id
    user_text = message.text

    if user_id not in dialogues:
        dialogues[user_id] = []

    dialogues[user_id].append({"role": "user", "content": user_text})
    if len(dialogues[user_id]) > 20:
        dialogues[user_id] = dialogues[user_id][-20:]

    bot.send_chat_action(user_id, 'typing')

    try:
        r = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Ты — helpful ассистент. Отвечай на русском, кратко и по делу."}
                ] + dialogues[user_id],
                "temperature": 0.7
            },
            timeout=(10, 30)
        )
        answer = r.json()["choices"][0]["message"]["content"]
        dialogues[user_id].append({"role": "assistant", "content": answer})

        if len(answer) <= 4096:
            bot.send_message(user_id, answer)
        else:
            for i in range(0, len(answer), 4096):
                bot.send_message(user_id, answer[i:i + 4096])
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Ошибка: {e}")

def run_bot():
    bot.infinity_polling()

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    threading.Thread(target=run_bot, daemon=True).start()
    # Запускаем веб-сервер (Render требует, чтобы слушал порт)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
