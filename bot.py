import telebot
from config import *
from logic import DB_Manager
import wikipedia
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


bot = telebot.TeleBot(TOKEN)


wikipedia.set_lang('ru')

game = {}

def get_page(last_city):
    try:
        page = wikipedia.page(last_city)
        text = wikipedia.summary(last_city)
        return page, text
    except wikipedia.exceptions.PageError:
        return None
    except wikipedia.exceptions.DisambiguationError:
        return None

def stop_game(text, message):
    chat_id = message.chat.id
    score = game[chat_id]['score']
    manager.new_score(score, chat_id)
    total_score = manager.get_score(chat_id)
    max_score = manager.get_max_score(chat_id)
    text += f"\nИгра окончена ⛔️\nСчёт за игру: {score}\nОбщий счёт: {total_score}"
    if score > max_score:
        manager.new_max_score(chat_id, score)
        text += '\nНовый рекорд!🏆'
    bot.send_message(chat_id, text)
    del game[chat_id]

def gen_markup(chat_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Узнать", callback_data=f'cb_search_{chat_id}'), InlineKeyboardButton("На карте", callback_data=f'cb_map_{chat_id}'))
    print(chat_id)
    return markup

def bot_move(message):
    chat_id = message.chat.id
    score = game[chat_id]['score']
    last_city = game[chat_id]['last_city']
    used_cities = game[chat_id]['used_cities']
    bot_city = manager.get_city(last_city, used_cities)
    if bot_city is not None:
        bot.send_message(chat_id, bot_city, reply_markup=gen_markup(chat_id))
        game[chat_id]['used_cities'].add(bot_city)
        game[chat_id]['last_city'] = bot_city
        print(used_cities)
    else:
        manager.new_score(score, chat_id)
        total_score = manager.get_score(chat_id)
        bot.send_message(chat_id, f"Я не знаю города на эту букву. Ты победил! 🏆\nСчёт за игру: {score}\nОбщий счёт: {total_score}")
        del game[chat_id]
        return
    
def city_map(chat_id, city):
    bot.send_chat_action(chat_id=chat_id, action='typing')

    if manager.create_grapf(city, chat_id):
        bot.send_chat_action(chat_id, 'upload_photo')
        with open(f'images/{chat_id}.png', 'rb') as photo:
            bot.send_photo(chat_id, photo, f'Город {city} на карте 🗺')
    else:
        bot.send_message(chat_id, 'Не удалось найти информацию о городе ⛔️')

def city_info(chat_id, last_city):
    try:
        wiki = wikipedia.summary(last_city)
        wiki = wikipedia.summary(f'город {last_city}')
        text = wiki.split(".")[0] + "." + wiki.split(".")[1] + "." + wiki.split(".")[2] + "."
        bot.send_message(chat_id, text)
    except wikipedia.exceptions.PageError:
        bot.send_message(chat_id, 'Не удалось найти информацию о городе ⛔️')
    except wikipedia.exceptions.DisambiguationError:
        bot.send_message(chat_id, 'Не удалось найти информацию о городе ⛔️')
    

@bot.message_handler(commands=['help'])
def help(message):
    chat_id = message.chat.id
    if chat_id in game:
        stop_game('', message)
    text = '''- - - - - - СПИСОК КОМАНД - - - - - -

/help - список команд ❔

/start - начать игру 🌎

/stop - закончить игру ⛔️

/rating - рейтинг 🏆

/score - ваш счет 📝

/map Город - город на карте мира 🗺

/info - информация о городе 🔎

- - - - - - - - - - - - - - - - - - - - - - - - - - - -'''
    bot.send_message(chat_id, text)

@bot.message_handler(commands=['start'])
def start_game(message):
    chat_id = message.chat.id
    username = message.from_user.username
    if chat_id not in manager.get_users():
        manager.add_user(chat_id, username)
    if chat_id in game:
        # bot.send_message(chat_id, f"Игра уже началась! Последний город: {game[chat_id]['last_city'][0]}")
        stop_game('', message)
        start_game(message)
    else:
        game[chat_id] = {
            'user': username,
            'last_city': '',
            'used_cities': set(),
            'score': 0,
        }
        bot.send_message(chat_id, "Игра началась!")
        bot_move(message)

@bot.message_handler(commands=['stop'])
def stop(message):
    chat_id = message.chat.id
    if chat_id not in game:
        bot.send_message(chat_id, "Вы ещё не начали игру ⛔️ /help, чтобы узнать команды")
    else:
        stop_game('', message)

@bot.message_handler(commands=['rating'])
def total_rating(message):
    chat_id = message.chat.id
    if chat_id in game:
        stop_game('', message)
    name = message.from_user.username
    users = manager.get_total_rating()
    text = '- - - - - - - РЕЙТИНГ - - - - - - -\n'
    print(users)
    for x, user in enumerate(users):
        print(user)
        text += f'\n{x+1}.   {user[1]}   -   {user[2]}\n'
    text += '\n- - - - - - - - - - - - - - - - - - - - - -\n'
    print(users)
    for user in users:
        if chat_id not in user:
            user_in_rating = False
        else:
            user_in_rating = True
            break
    if user_in_rating == False:
        user_rating = manager.get_user_rating(chat_id)
        name = message.from_user.username
        score = manager.get_score(chat_id)
        text += f'\n{user_rating}.   {name}   -   {score}'

    print(text)
    bot.send_message(chat_id, text)

@bot.message_handler(commands=['map'])
def map(message):
    chat_id = message.chat.id
    if chat_id in game:
        stop_game('', message)
    bot.send_chat_action(chat_id, 'typing')
    city = message.text.replace('/map', '').lstrip()
    bot_message = bot.send_message(chat_id, f'Ищу информацию о городе {city}... 🔎')
    city_map(chat_id, city)
    bot.delete_message(chat_id, bot_message.message_id)

@bot.message_handler(commands=['info'])
def info(message):
    chat_id = message.chat.id
    if chat_id in game:
        stop_game('', message)
    bot.send_chat_action(chat_id, 'typing')
    city = message.text.replace('/info', '').lstrip()
    bot_message = bot.send_message(chat_id, f'Ищу информацию о городе {city}... 🔎')
    city_info(chat_id, city)
    bot.delete_message(chat_id, bot_message.message_id)

@bot.message_handler(commands=['score'])
def score(message):
    chat_id = message.chat.id
    if chat_id in game:
        stop_game('', message)
    total_score = manager.get_score(chat_id)
    max_score = manager.get_max_score(chat_id)
    rating = manager.get_user_rating(chat_id)
    print(rating)
    text = f'''- - - - - - {message.from_user.username} - - - - - -

Общий счёт: {total_score}

Рекорд: {max_score}

Место в рейтинге: {rating if rating > 5 else f'{rating} 🏆'}

- - - - - - - - - - - - - - - - - - - - - -
'''
    bot.send_message(chat_id, text)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # if call.data.startswith("cb"):
    chat_id = int(call.data.split("_")[2])
    last_city = game[chat_id]['last_city']
    print(last_city)
    bot_message = bot.send_message(chat_id, f'Ищу информацию о городе {last_city}... 🔎')
    bot.send_chat_action(chat_id, 'typing')
    if call.data.startswith("cb_search"):
        city_info(chat_id, last_city)
        bot.delete_message(chat_id, bot_message.message_id)
    elif call.data.startswith("cb_map"):
        city_map(chat_id, last_city)
        bot.delete_message(chat_id, bot_message.message_id)
        

@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def handle_message(message):
    chat_id = message.chat.id
    if chat_id not in game:
        bot.send_message(chat_id, "Вы ещё не начали игру ⛔️ /help, чтобы узнать команды")
        return
    user_city = message.text.strip()
    score = game[chat_id]['score']
    text = ''
    used_cities = game[chat_id]['used_cities']
    last_letter = game[chat_id]['last_city'][-1].lower()
    print(used_cities)
    
    print(last_letter)
    if manager.check_city(user_city) == False:
        text += f"Такого города в моей базе нет!"
        stop_game(text, message)
        return
    if user_city in used_cities:
        text += f"Этот город уже был назван!"
        stop_game(text, message)
        return
    if last_letter in ['ь', 'ы', 'ъ']:
        last_letter = game[chat_id]['last_city'][-2].lower()
    
    if user_city[0].lower() != last_letter:        
        text += f"Неверная буква!"
        stop_game(text, message)
        return
    else:
        game[chat_id]['last_city'] = user_city
        game[chat_id]['used_cities'].add(user_city)
        game[chat_id]['score'] = score + 1
        print(game[chat_id]['score'])
        bot_move(message)




if __name__=="__main__":
    manager = DB_Manager(DATABASE)
    bot.polling()