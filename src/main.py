import sqlite3
import telebot
import requests
import time
from telebot import types

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

    us_id = message.from_user.id
    check_streams_for_user(message, us_id)


@bot.message_handler(commands=['help'])
def message_help(message):
    bot.send_message(message.chat.id, """How it works:
0) ☰ You choose 'Menu'
1) 🏁 You selecting 'Login'
2) ⌨️ Typing streamer's nickname or URL
3) 📃 Get information about him: Online/Offline, Followers, URL
4) ✔️ Follow him in this bot or just leave it""")


@bot.message_handler(commands=['login'])
def message_login(message):
    us_id = message.from_user.id
    if not user_exists(user_id=us_id):
        create_user(message, user_id=us_id)
        bot.send_message(message.chat.id, f"New user with id:{message.from_user.id} have been created!")
    else:
        bot.send_message(message.chat.id, "User already exists.")


@bot.message_handler(commands=['menu'])
def message_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    login_key = types.KeyboardButton("🏁 Login")
    find_key = types.KeyboardButton("🔍 Find streamer")
    my_account_key = types.KeyboardButton("🔑 My account")
    help_key = types.KeyboardButton("❔ Help")

    markup.add(login_key, find_key, my_account_key, help_key)
    bot.send_message(message.chat.id, "☰ Menu", reply_markup=markup)


@bot.message_handler(commands=['find'])
def message_find(message):
    bot.send_message(message.chat.id, "Write a streamer's nickname on Twitch")
    bot.register_next_step_handler(message, find_streamer)


@bot.message_handler(commands=['account'])
def message_account(message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, f"Your account:\nID: {message.from_user.id}\nYour followings: {count_followings(user_id)}")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    login_key = types.KeyboardButton("🔢 Followings")
    find_key = types.KeyboardButton("➖ Unfollow streamer")
    menu_key = types.KeyboardButton("☰ Menu")

    markup.add(login_key, find_key, menu_key)
    bot.send_message(message.chat.id, "🔑 My account", reply_markup=markup)


@bot.message_handler(commands=['followings'])
def message_followings(message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, f"You have subscriptions on {count_followings(user_id)}:\n{print_followings(user_id)}")


@bot.message_handler(commands=['unfollow'])
def message_unfollow(message):
    bot.send_message(message.chat.id, "Write a streamer's nickname to unfollow")
    bot.register_next_step_handler(message, unfollow)


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
        elif message.text == '🔑 My account':
            message_account(message)
        elif message.text == '🔢 Followings':
            message_followings(message)
        elif message.text == '➖ Unfollow streamer':
            message_unfollow(message)
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


def count_followings(user_id):
    cursor.execute('SELECT COUNT(streamer_id) FROM subscription WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return 0


def print_followings(user_id):
    cursor.execute('SELECT streamer_name FROM subscription '
                   'JOIN streamers ON subscription.streamer_id = streamers.streamer_id '
                   'WHERE user_id = ?', (user_id,))
    subscriptions = cursor.fetchall()
    if subscriptions:
        subscribed_streamers = [sub[0] for sub in subscriptions]
        return "\n".join(subscribed_streamers)
    else:
        return None  # Если пользователь не подписан ни на одного стримера, возвращаем None


def unfollow(message):
    user_id = message.from_user.id
    streamer_name = message.text.lower()
    cursor.execute('SELECT streamer_id FROM streamers WHERE streamer_name = ?', (streamer_name,))
    streamer_id = cursor.fetchone()
    if streamer_id:
        cursor.execute('DELETE FROM subscription WHERE user_id = ? AND streamer_id = ?', (user_id, streamer_id[0]))
        conn.commit()
        bot.send_message(message.chat.id, f"You have been successfully unfollowed from {streamer_name}.")
    else:
        bot.send_message(message.chat.id, f"There is no streamer with name: {streamer_name}.")


def get_subscribed_streamers(user_id):
    cursor.execute('SELECT streamer_name FROM subscription '
                   'JOIN streamers ON subscription.streamer_id = streamers.streamer_id '
                   'WHERE subscription.user_id = ?', (user_id,))
    subscribed_streamers = cursor.fetchall()
    return [row[0] for row in subscribed_streamers]


def is_already_notified(streamer_name):
    cursor.execute('SELECT online FROM streamers WHERE streamer_name = ?', (streamer_name.lower(),))
    result = cursor.fetchone()
    if result:
        return result[0] == 1
    else:
        return False


def set_streamer_online_status(streamer_name, online):
    cursor.execute('UPDATE streamers SET online = ? WHERE streamer_name = ?', (int(online), streamer_name.lower()))
    conn.commit()


def check_streams_for_user(message, user_id):
    while True:
        # Получаем список подписок пользователя
        subscribed_streamers = get_subscribed_streamers(user_id)

        # Проверяем каждого подписанного стримера
        for streamer_name in subscribed_streamers:
            access_token = get_twitch_access_token()  # Получаем токен для каждой проверки
            is_live = check_streamer_online(access_token, streamer_name)
            if is_live:
                # Проверяем, было ли уже отправлено уведомление о начале стрима
                if not is_already_notified(streamer_name):
                    user_data = get_user_data(access_token, streamer_name)
                    user_url = f'https://www.twitch.tv/{streamer_name}'
                    bot.send_photo(message.chat.id, user_data['profile_image_url'], caption=f"🔴{streamer_name} is LIVE NOW\nTwitch profile: {user_url}")
                    # Обновляем статус стримера в базе данных
                    set_streamer_online_status(streamer_name, True)
            else:
                # Обновляем статус стримера в базе данных
                set_streamer_online_status(streamer_name, False)

        # Задержка перед следующей проверкой
        time.sleep(10)  # в секундах
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
                    else:
                        bot.send_message(message.chat.id, f"Unable to get information about {nickname}.")
                else:
                    bot.send_message(message.chat.id, f"There is no Twitch streamer with the name {nickname}.")
            else:
                bot.send_message(message.chat.id, "Error getting Twitch access token.")
        else:
            bot.send_message(message.chat.id, "Please log in using the '🏁 Login' option.")
    elif message.text == "🔍 Find streamer":
        message_find(message)
    elif message.text == "🔑 My account":
        message_account(message)
    elif message.text == "☰ Menu":
        message_menu(message)


def subscribe_to_streamer(user_id: int, streamer_name: str):
    # Получаем streamer_id по имени стримера
    cursor.execute('SELECT streamer_id FROM streamers WHERE streamer_name = ?',
                   (streamer_name.lower(),))
    existing_streamer = cursor.fetchone()

    if existing_streamer:
        # Если стример существует, проверяем, подписан ли пользователь уже
        cursor.execute('SELECT * FROM subscription WHERE user_id = ? AND streamer_id = ?',
                       (user_id, existing_streamer[0]))
        existing_subscription = cursor.fetchone()

        if existing_subscription:
            bot.send_message(user_id, f"You are already subscribed to {streamer_name}.")
            return
    else:
        # Если стримера с таким именем нет, добавляем его в таблицу streamers
        cursor.execute('INSERT INTO streamers (streamer_name, streamer_url) VALUES (?, ?)',
                       (streamer_name.lower(), f'https://www.twitch.tv/{streamer_name.lower()}'))
        streamer_id = cursor.lastrowid  # Получаем автоматически сгенерированный streamer_id
    if not existing_streamer:
        streamer_id = cursor.lastrowid
    else:
        streamer_id = existing_streamer[0]

    # Добавляем запись в таблицу subscription
    cursor.execute('INSERT INTO subscription (user_id, streamer_id) VALUES (?, ?)',
                   (user_id, streamer_id))
    conn.commit()
    # Отправляем сообщение о успешной подписке
    bot.send_message(user_id,
                     f"Now you are following {streamer_name}. You will receive notifications when he start streaming.")


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