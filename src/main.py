import sqlite3
import telebot
from telebot import types

TOKEN = "6750520093:AAGtz40xJG2ivepaAtjU5x46FQoEKP-bR84"
bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect('../db/database', check_same_thread=False)
cursor = conn.cursor()


def create_user(message, user_id: str):
    bot.send_message(message.chat.id, f"отправил айди {user_id}")
    cursor.execute(
        'INSERT INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()


@bot.message_handler(commands=["start"])
def message_start(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("🏁 Begin")
    item2 = types.KeyboardButton("❔ Help")
    markup.add(item1, item2)

    bot.send_message(message.chat.id, f"""🟣Hello {message.from_user.first_name}, this is Telegram bot for tracking your favorite streamers on Twitch💜
Type '🏁 Begin' to get started!""", reply_markup = markup)


@bot.message_handler(commands=['help'])
def message_help(message):
    bot.send_message(message.chat.id, """How it works:
1) 🏁 You selecting 'Begin'
2) ⌨️ Typing streamer's nickname or URL
3) 📃 Get information about him: Online/Offline, Followers, URL
4) ✔️ Follow him in this bot or just leave it""")



@bot.message_handler(content_types=['text'])
def get_text_message(message):
    if message.chat.type == 'private':
        if message.text == '❔ Help':
            bot.send_message(message.chat.id, message_help(message))
        elif message.text == '🏁 Begin':
            try:
                bot.send_message(message.chat.id, "должен был добавить")
                us_id = message.from_user.id
                create_user(message, user_id=us_id)
            except Exception:
                return "WTF"



if __name__ == '__main__':
	bot.infinity_polling()