from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

button_top = KeyboardButton('Топ 100')
button_categories = KeyboardButton('Категории')
button_random = KeyboardButton('Рандомный фильм')

button_main = KeyboardButton("Назад")
button_random_categories = KeyboardButton("Выбрать случайную категорию")

main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
main_keyboard.insert(button_top).insert(button_categories).insert(button_random)

categories_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
categories_keyboard.insert(button_main).insert(button_random_categories)
