import os
import telebot
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_KEY")

bot = telebot.TeleBot(BOT_TOKEN, request_timeout=30)

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

if __name__ == '__main__':
    print("Bot started...")
    bot.infinity_polling()
