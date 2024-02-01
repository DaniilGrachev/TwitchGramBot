import sqlite3
import telebot
import requests
from telebot import types
from typing import Tuple

TOKEN = "6750520093:AAGtz40xJG2ivepaAtjU5x46FQoEKP-bR84"
bot = telebot.TeleBot(TOKEN)

CLIENT_ID = 'sn586pl402dj3vk22280dng9ijaa6g'
CLIENT_SECRET = '0mgddkx9xu4oq9iay9r3ptbln2rm9w'

conn = sqlite3.connect('../db/database', check_same_thread=False)
cursor = conn.cursor()


# -------------------------------------------------------------------------------DECORATORS-------------------------------------------------------------------------------
@bot.message_handler(commands=["start"])
def message_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu_key = types.KeyboardButton("☰ Menu")
    help_key = types.KeyboardButton("❔ Help")
    markup.add(menu_key, help_key)

    bot.send_message(message.chat.id, f"""🟣Hello {message.from_user.first_name}, this is Telegram bot for tracking your favorite streamers on Twitch💜
Type '🏁 Login' to get started!""", reply_markup=markup)


@bot.message_handler(commands=['help'])
def message_help(message):
    bot.send_message(message.chat.id, """How it works:
0) ☰ You choose 'Menu'
1) 🏁 You selecting 'Login'
2) ⌨️ Typing streamer's nickname or URL
3) 📃 Get information about him: Online/Offline, Followers, URL
4) ✔️ Follow him in this bot or just leave it""")


@bot.message_handler(commands=['menu'])
def message_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    login_key = types.KeyboardButton("🏁 Login")
    find_key = types.KeyboardButton("🔍 Find streamer")
    my_account_key = types.KeyboardButton("🔑 My account")
    help_key = types.KeyboardButton("❔ Help")

    markup.add(login_key, find_key, my_account_key, help_key)
    bot.send_message(message.chat.id, "☰ Menu", reply_markup=markup)


@bot.message_handler(commands=['login'])
def message_login(message):
    us_id = message.from_user.id
    if not user_exists(user_id=us_id):
        create_user(message, user_id=us_id)
        bot.send_message(message.chat.id, f"New user with id:{message.from_user.id} have been created!")
    else:
        bot.send_message(message.chat.id, "User already exists.")


@bot.message_handler(commands=['find'])
def message_find(message):
    bot.send_message(message.chat.id, "Write a streamer's nickname on Twitch")
    bot.register_next_step_handler(message, find_streamer)


@bot.message_handler(content_types=['text'])
def get_messages(message):
    if message.chat.type == 'private':
        if message.text == '❔ Help':
            message_help(message)
        elif message.text == '☰ Menu':
            message_menu(message)
        elif message.text == '🏁 Login':
            message_login(message)
        elif message.text == '🔍 Find streamer':
            message_find(message)
        else:
            bot.send_message(message.chat.id, "Sorry, I don't this command")
# -------------------------------------------------------------------------------DECORATORS-------------------------------------------------------------------------------


# -------------------------------------------------------------------------------FUNCTIONS-------------------------------------------------------------------------------
# --------------------------USER--------------------------
def user_exists(user_id):
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    return cursor.fetchone() is not None


def create_user(message, user_id: str):
    cursor.execute(
        'INSERT INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
# --------------------------USER--------------------------


# --------------------------ACCESS--------------------------
def get_twitch_access_token():
    url = 'https://id.twitch.tv/oauth2/token'
    params = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }

    response = requests.post(url, params=params)
    data = response.json()

    if 'access_token' in data:
        return data['access_token']
    else:
        print('Error getting access token:', data)
        return None
# --------------------------ACCESS--------------------------


# --------------------------STREAMER--------------------------
def check_streamer_existence(access_token, username):
    url = f'https://api.twitch.tv/helix/users?login={username}'
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    return 'data' in data and data['data']


def find_streamer(message):
    nickname = message.text
    access_token = get_twitch_access_token()

    if access_token:
        if check_streamer_existence(access_token, nickname):
            is_live = check_streamer_online(access_token, nickname)
            user_data = get_user_data(access_token, nickname)

            # Создаем новую клавиатуру для данной ситуации
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            follow_key = types.KeyboardButton("📢 Follow")
            find_key = types.KeyboardButton("🔍 Find streamer")
            my_account_key = types.KeyboardButton("🔑 My account")
            menu_key = types.KeyboardButton("☰ Menu")

            markup.add(follow_key, find_key, my_account_key, menu_key)
            bot.reply_to(message, f"Searching for streamer: {nickname}", reply_markup=markup)

            if is_live:
                bot.send_message(message.chat.id, f"{nickname} is currently live on Twitch.")
            else:
                bot.send_message(message.chat.id, f"{nickname} is currently offline on Twitch.")
            if user_data:
                user_url = f'https://www.twitch.tv/{nickname}'
                bot.send_photo(message.chat.id, user_data['profile_image_url'], caption=f"Twitch profile: {user_url}")
                # Регистрируем обработчик для кнопки "📢 Follow"
                bot.register_next_step_handler(message, lambda m: follow_streamer(m, nickname))
        else:
            bot.send_message(message.chat.id, f"There is no Twitch streamer with the name {nickname}.")


def follow_streamer(message, nickname: str):
    if message.text == "📢 Follow":
        user_id = message.from_user.id
        if user_exists(user_id):
            access_token = get_twitch_access_token()

            if access_token:
                if check_streamer_existence(access_token, nickname):
                    user_data = get_user_data(access_token, nickname)
                    if user_data:
                        subscribe_to_streamer(user_id, nickname)
                        bot.send_message(message.chat.id, f"You are now following {nickname}. You will receive notifications when they start streaming.")
                    else:
                        bot.send_message(message.chat.id, f"Unable to get information about {nickname}.")
                else:
                    bot.send_message(message.chat.id, f"There is no Twitch streamer with the name {nickname}.")
            else:
                bot.send_message(message.chat.id, "Error getting Twitch access token.")
        else:
            bot.send_message(message.chat.id, "Please log in using the '🏁 Login' option.")


def subscribe_to_streamer(user_id: int, streamer_name: str):
    # Добавляем данные в таблицу streamers
    cursor.execute('INSERT INTO streamers (streamer_name, streamer_url) VALUES (?, ?)',
                   (streamer_name.lower(), f'https://www.twitch.tv/{streamer_name.lower()}'))
    streamer_id = cursor.lastrowid  # Получаем автоматически сгенерированный streamer_id

    # Получаем текущее значение streamers_id для пользователя
    cursor.execute('SELECT streamers_id FROM users WHERE user_id = ?', (user_id,))
    current_streamers_id = cursor.fetchone()

    # Обновляем streamers_id для пользователя в таблице users
    if current_streamers_id and current_streamers_id[0]:  # Если current_streamers_id не пусто
        new_streamers_id = f"{current_streamers_id[0]}, {streamer_id}"
    else:
        new_streamers_id = str(streamer_id)

    cursor.execute('UPDATE users SET streamers_id = ? WHERE user_id = ?', (new_streamers_id, user_id))
    conn.commit()


def check_streamer_online(access_token, username):
    url = f'https://api.twitch.tv/helix/streams?user_login={username}'
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    return 'data' in data and data['data']


def get_user_data(access_token, username):
    url = f'https://api.twitch.tv/helix/users?login={username}'
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    if 'data' in data and data['data']:
        return data['data'][0]  # Возвращаем данные первого пользователя (должен быть только один)
    else:
        return None
# --------------------------STREAMER--------------------------
# -------------------------------------------------------------------------------FUNCTIONS-------------------------------------------------------------------------------


# ---------MAIN---------
if __name__ == '__main__':
    bot.infinity_polling()