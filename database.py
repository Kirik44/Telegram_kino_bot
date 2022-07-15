import random
import sqlite3
from main import logger
import requests
from bs4 import BeautifulSoup

url = 'https://www.kinoafisha.info/rating/movies/?page='

dbSQL = sqlite3.connect('Database.db', check_same_thread=False)
sql = dbSQL.cursor()

sql.execute("""CREATE TABLE IF NOT EXISTS Rating(
    Id INTEGER,
    Name TEXT,
    Genre Text,
    Rating Text,
    Data Text,
    ImageURL,
    FilmsURL
)""")

sql.execute("""CREATE TABLE IF NOT EXISTS Genres(
    Id INTEGER,
    Genre Text   
)""")
dbSQL.commit()

logger.success("Database Init")


def get_page(page_number):  # обновление информации в базе данных
    response = requests.get(url + str(page_number))
    soup = BeautifulSoup(response.text, features="html.parser")

    names = soup.find_all('a', class_='movieItem_title')
    positions = soup.find_all('span', class_='movieItem_position')
    rating_numbers = soup.find_all('span', class_='rating_num')
    genres = soup.find_all('span', class_='movieItem_genres')
    years = soup.find_all('span', class_='movieItem_year')
    images = soup.find_all('img', class_='picture_image', title=True)

    for i in range(0, len(names)):
        name = names[i].text
        position = positions[i].text
        rating_num = rating_numbers[i].text
        genre = genres[i].text
        year = years[i].text
        image = images[i]['data-picture']
        film_url = names[i]["href"]

        items = (position, name, genre, rating_num, year, image, film_url)

        sql.execute(f"INSERT INTO Rating VALUES (?, ?, ?, ?, ?, ?, ?)", items)


def update_database():  # Получение информаци со страницы сайта
    logger.info("The database update procedure has been started")

    sql.execute("""DELETE FROM Rating""")
    sql.execute("""DELETE FROM Genres""")

    for i in range(0, 20):
        get_page(i)

    dbSQL.commit()

    sql.execute("""SELECT Genre FROM Rating""")
    genres = sql.fetchall()

    genre = []
    genre.clear()

    for item in genres:
        item = str(item)
        item = item.replace(" ", "")
        item = item.replace("(", "")
        item = item.replace(")", "")
        item = item.replace("'", "")

        values = item.split(",")

        for value in values:
            if_not_genre = True

            for _genre in genre:
                if value == _genre:
                    if_not_genre = False

            if if_not_genre:
                if value != "":
                    genre.append(value)

    i = 0
    for items in genre:
        i = i + 1
        sql.execute(f"INSERT INTO Genres VALUES (?, ?)", (i, str(items)))

    dbSQL.commit()

    logger.success("The database has been updated successfully")


def get_top():  # Вывод топ 100 фильмов
    string = ""

    sql.execute("""SELECT * FROM Rating WHERE Id < 101""")
    all_results = sql.fetchall()

    for item in all_results:
        string += str(item[0]) + ': ' + '<a href="' + str(item[6]) + '">' + str(item[1]) + '</a>\n'

    return string


def get_film(value):    # Получение одного фильма по id
    sql.execute(f"SELECT * FROM Rating WHERE Id = '" + str(value) + "'")
    item = sql.fetchone()
    return item


def get_categories():   # Подучение списка всех категорий
    sql.execute("""SELECT * FROM Genres""")
    categories = sql.fetchall()

    return categories


def get_value_categories():     # Получение числа категорий
    sql.execute("""SELECT * FROM Genres""")
    categories = sql.fetchall()
    return len(categories)


def get_one_category(value):   # Получение одной категории по id
    sql.execute("SELECT * FROM Genres WHERE Id = " + str(value))
    categories = sql.fetchone()
    return str(categories[1])


def get_list_films_category(category, quantity):       # Получение списка фильмов с выбранной категории
    sql.execute("""SELECT * FROM Rating""")
    request = sql.fetchall()

    result = []
    result.clear()
    i = 0

    for item in request:
        if category in str(item[2]):
            i = i + 1
            result.append(item)
            if i >= quantity:
                break

    return result


def get_random_film_select_category(category):   # Получить рандомный фильм из выбранной категории
    films = get_list_films_category(category, 1000)

    quantity_film = len(films)

    if quantity_film == 0:
        return None

    if quantity_film == 1:
        return films[0]

    random_id = random.randint(0, quantity_film - 1)

    return films[random_id]
