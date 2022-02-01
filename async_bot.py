from aiogram import Bot, Dispatcher, executor, types
from config import host, user, password, db_name
from aiogram.dispatcher.filters import Text
import psycopg2

bot = Bot(token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

new_cats = []

connection = psycopg2.connect(
    host=host,
    user=user,
    password=password,
    database=db_name
)
connection.autocommit = True

@dp.message_handler(commands='start')
async def start(message: types.Message):
    start_buttons = ["Лента", "О'кей", "Перекресток"]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*start_buttons)

    await message.answer('Выберите магазин', reply_markup=keyboard)

@dp.message_handler()
async def cats(message: types.Message):

    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT cat_name FROM retailers_cats_subcats WHERE retailer_name = ('{message.text}');"
        )
        cats = sorted(set(cursor.fetchall()))

    for cat in cats:
        cat = str(cat).lstrip("('").rstrip(",)'")
        new_cats.append(cat)

    buttons = []
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    for cat in new_cats:
        btn = types.KeyboardButton(f"{cat}")
        buttons.append(btn)
    markup.add(*buttons)
    await message.answer(message.chat.id, 'Выберите категорию', reply_markup=markup)



def main():
    executor.start_polling(dp)

if __name__ == '__main__':
    main()