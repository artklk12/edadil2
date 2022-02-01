import time

from telebot import types
import config
import dbworker
from config import host, user, password, db_name, token
import psycopg2
import telebot

bot = telebot.TeleBot(token)


connection = psycopg2.connect(
    host=host,
    user=user,
    password=password,
    database=db_name
)
connection.autocommit = True

retailers_bot = {
    "Лента": "lenta-giper",
    "Перекрёсток": "perekrestok",
    "О'Кей": "okmarket-giper"
}
# @bot.message_handler(commands=["start"])
@bot.message_handler(content_types=["text"])
def start(message):
    retailers_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Лента")
    btn2 = types.KeyboardButton("Перекрёсток")
    btn3 = types.KeyboardButton("О'Кей")
    retailers_markup.add(btn1, btn2, btn3)

    send = bot.send_message(message.chat.id, "Выберите магазин", reply_markup=retailers_markup)
    # dbworker.set_state(message.chat.id, config.States.S_CHOOSE_CAT.value)
    bot.register_next_step_handler(send, cats_handler)
#
# @bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_CHOOSE_CAT.value)
def cats_handler(message):

    new_cats = []
    retailers_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Лента")
    btn2 = types.KeyboardButton("Перекрёсток")
    btn3 = types.KeyboardButton("О'Кей")
    retailers_markup.add(btn1, btn2, btn3)

    try:
        selected_retailer = retailers_bot[message.text]
    except Exception:
        bot.send_message(message.chat.id, "Используйте клавиатуру", reply_markup=retailers_markup)

    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT cat_name FROM retailers_cats_subcats WHERE retailer_name = ('{selected_retailer}');"
        )
        cats = sorted(set(cursor.fetchall()))

    for cat in cats:
        cat = str(cat).lstrip("('").rstrip(",)'")
        new_cats.append(cat)

    buttons = []
    cats_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    for cat in new_cats:
        btn = types.KeyboardButton(f"{cat}")
        buttons.append(btn)
    cats_markup.add(*buttons)
    send = bot.send_message(message.chat.id, 'Выберите категорию', reply_markup=cats_markup)
    # dbworker.set_state(message.chat.id, config.States.S_CHOOSE_SUBCAT.value)
    bot.register_next_step_handler(send, subcats_handler, selected_retailer)

# @bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_CHOOSE_SUBCAT.value)
def subcats_handler(message, selected_retailer):

    selected_cat = message.text
    new_subcats = []

    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT subcat_name FROM retailers_cats_subcats WHERE (retailer_name, cat_name) = ('{selected_retailer}', '{selected_cat}');"
        )
        subcats = sorted(set(cursor.fetchall()))

    for subcat in subcats:
        subcat = str(subcat).lstrip("('").rstrip(",)'")
        new_subcats.append(subcat)

    buttons = []
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    for subcat in new_subcats:
        btn = types.KeyboardButton(f"{subcat}")
        buttons.append(btn)
    markup.add(*buttons)
    send = bot.send_message(message.chat.id, 'Выберите подкатегорию', reply_markup=markup)
    bot.register_next_step_handler(send, products_handler, selected_retailer)

def products_handler(message, selected_retailer):

    selected_subcat = message.text

#     back_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#     next = types.KeyboardButton("Дальше")
#     back = types.KeyboardButton("Назад")
#     back_markup.add(back, next)
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM products WHERE (fk_retailer, fk_subcat) = ('{selected_retailer}', '{selected_subcat}');"
        )
        products = sorted(set(cursor.fetchall()))

    for index, product in enumerate(products):
        card = f"{product[0].rstrip(',…')}\n" \
               f"Cтарая цена: {product[6]}\n" \
               f"Новая цена: {product[5]} 🔥\n" \
               f"Скидка {product[1]}\n" \
               f"{product[2]}"

        bot.send_message(message.chat.id, card)
        if index != 0 and index%20 == 0:
            time.sleep(3)

#             if message.text == "Дальше":
#                 pass
#             elif message.text == "Назад":
#                 break

bot.polling(none_stop=True)
