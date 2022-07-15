from datetime import datetime
import random
from aiogram.dispatcher.filters.state import State, StatesGroup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from babel.localtime import get_localzone
from loguru import logger

import btn
import database

TOKEN = "TOKEN"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


class BotStates(StatesGroup):
    MAIN_STATE = State()
    CATEGORIES_STATE = State()


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


@dp.message_handler(state='*', commands=['start'])
async def start_command(message: types.Message):
    await message.answer("Добро пожаловать " + str(message.from_user.first_name) + "!", reply_markup=btn.main_keyboard)
    await BotStates.MAIN_STATE.set()


@dp.callback_query_handler(text_startswith="category_", state='*')
async def callbacks_switch_category(call: types.CallbackQuery):
    category = str(call.data.split("_")[1])
    categories = database.get_categories()
    is_none = True

    for item in categories:
        if item[1] == str(category):
            is_none = False
            break

    if is_none:
        await call.message.answer("Произошла ошибка")
        logger.error("Категория не найдена, is_none = True")
        return

    keyboard = types.InlineKeyboardMarkup()

    logger.info(category)

    list_films = database.get_list_films_category(category, 9)

    for item in list_films:
        keyboard.insert(types.InlineKeyboardButton(text=str(item[1]),
                                                   callback_data="films_" + str(item[0])))

    keyboard.insert(types.InlineKeyboardButton(text="Случайный фильм", callback_data="randomFilms_" + str(category)))

    await call.message.answer("Выберите фильм", reply_markup=keyboard)
    await call.answer()


@dp.callback_query_handler(text_startswith="films_", state='*')
async def callbacks_switch_films(call: types.CallbackQuery):
    id_films = str(call.data.split("_")[1])
    logger.info(str(id_films))
    item = database.get_film(id_films)
    if len(item) == 0:
        await call.message.answer("Фильм не найден")
        return

    await bot.send_photo(call.message.chat.id, types.InputFile.from_url(str(item[5])),
                         '<a href="' + str(item[6] + '">' + str(item[1]) + '</a>' + "\nМесто в топе: " + str(item[0])
                                           + "\nЖанр: " + str(item[2]) + "\nРейтинг: " + str(item[3]) + "\nВыпущен "
                                           + str(item[4])), parse_mode=types.ParseMode.HTML)

    await call.answer()


@dp.callback_query_handler(text_startswith="randomFilms_", state='*')
async def callbacks_random_films(call: types.CallbackQuery):
    category = str(call.data.split("_")[1])
    logger.info(str(category))
    films = database.get_random_film_select_category(category)

    if films is None:
        await call.answer("Произошла ошибка")

    await bot.send_photo(call.message.chat.id, types.InputFile.from_url(str(films[5])),
                         '<a href="' + str(films[6] + '">' + str(films[1]) + '</a>' + "\nМесто в топе: " + str(films[0])
                                           + "\nЖанр: " + str(films[2]) + "\nРейтинг: " + str(films[3]) + "\nВыпущен "
                                           + str(films[4])), parse_mode=types.ParseMode.HTML)

    await call.answer()


@dp.message_handler(state='*')      # реагирование на команды
async def main_menu(message: types.Message):
    argument = str(message.text)

    if message.text == 'Категории':
        list_categories = database.get_categories()
        if len(list_categories) == 0:
            logger.error("len(list_categories) == 0")
            await message.answer("Error")
            return

        keyboard = types.InlineKeyboardMarkup(row_width=2)
        for item in list_categories:
            keyboard.insert(types.InlineKeyboardButton(text=str(item[1]),
                                                       callback_data="category_" + str(item[1])))

        await BotStates.CATEGORIES_STATE.set()
        await message.answer("Вот список доступных категорий", reply_markup=keyboard)
        await message.answer("Выберите категорию , которую хотите посмотреть", reply_markup=btn.categories_keyboard)

    elif message.text == 'Рандомный фильм':
        item = database.get_film(random.randint(1, 2000))
        await bot.send_photo(message.chat.id,
                             types.InputFile.from_url(str(item[5])),
                             '<a href="' + str(
                                 item[6] + '">' + str(item[1]) + '</a>' + "\nМесто в топе: " + str(item[0])
                                 + "\nЖанр: " + str(item[2]) + "\nРейтинг: " + str(item[3]) + "\nВыпущен "
                                 + str(item[4])), parse_mode=types.ParseMode.HTML)

    elif message.text == 'Топ 100':
        await message.answer(database.get_top(), parse_mode=types.ParseMode.HTML)

    elif argument == 'Выбрать случайную категорию':

        random_id = random.randint(0, database.get_value_categories() - 1)
        category = database.get_one_category(random_id)
        logger.info(category)

        keyboard = types.InlineKeyboardMarkup()

        list_films = database.get_list_films_category(category, 9)

        for item in list_films:
            keyboard.insert(types.InlineKeyboardButton(text=str(item[1]),
                                                       callback_data="films_" + str(item[0])))

        keyboard.insert(types.InlineKeyboardButton(text="Случайный фильм",
                                                   callback_data="randomFilms_" + str(category)))

        await message.answer("Категория: " + str(category), reply_markup=keyboard)

    elif argument == 'Назад':
        await message.answer("Good", reply_markup=btn.main_keyboard)
        await BotStates.MAIN_STATE.set()

    else:
        await BotStates.MAIN_STATE.set()
        await message.answer("Команда не распознана", reply_markup=btn.main_keyboard)


if __name__ == '__main__':
    logger.info("Launch")

    scheduler = AsyncIOScheduler(timezone=str(get_localzone()))
    scheduler.add_job(database.update_database, 'interval', days=1, next_run_time=datetime.now())
    scheduler.start()

    executor.start_polling(dp, on_shutdown=shutdown)
