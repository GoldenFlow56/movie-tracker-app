import streamlit as st
import json
import requests

# Путь к JSON-файлу с базой (создай файл movies.json с твоей базой)
DATA_FILE = 'movies.json'

# Функция для загрузки данных
def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'movies': [], 'series': [], 'cartoons': []}  # Разделение на категории

# Функция для сохранения данных
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Функция для получения данных из TMDb API
def get_movie_details(title, api_key, is_series=False):
    if not api_key:
        return {'year': 'Неизвестно', 'genre': 'Неизвестно', 'parts': 1}
    
    base_url = "https://api.themoviedb.org/3/search/" + ("tv" if is_series else "movie")
    params = {'api_key': api_key, 'query': title, 'language': 'ru'}
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
            movie = results[0]
            genres = movie.get('genre_ids', [])
            # Для жанров нужно отдельный запрос или маппинг, но для простоты используем базовые
            genre_str = 'Неизвестно'  # Можно улучшить
            year = movie.get('release_date', '')[:4] or movie.get('first_air_date', '')[:4]
            parts = movie.get('number_of_seasons', 1) if is_series else 1
            return {'year': year, 'genre': genre_str, 'parts': parts}
    return {'year': 'Неизвестно', 'genre': 'Неизвестно', 'parts': 1}

# Базовая стилизация (CSS)
st.markdown("""
    <style>
    /* Фон и текст */
    .stApp {
        background-color: #f0f4f8;
        color: #333;
    }
    /* Заголовки */
    h1, h2, h3 {
        color: #007bff;  /* Синий цвет */
        font-family: 'Arial', sans-serif;
        font-weight: bold;
    }
    /* Кнопки */
    .stButton > button {
        background-color: #007bff;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
    }
    .stButton > button:hover {
        background-color: #0056b3;
    }
    /* Текстовые поля */
    .stTextInput > div > div > input {
        border: 1px solid #007bff;
        border-radius: 5px;
    }
    /* Блоки */
    .css-1y4p8pa {  /* Контейнеры */
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Основной интерфейс
st.title('MovieTracker: Твоё хранилище фильмов, сериалов и мультфильмов')

# Секция для ввода API-ключа (для каждого пользователя)
st.header('Настройка API-ключа TMDb')
st.markdown("""
Чтобы приложение автоматически подтягивало детали (год, жанр, части), введите ваш API-ключ от TMDb.  
**Инструкция по получению ключа (бесплатно, 2 минуты):**  
1. Зарегистрируйтесь на [themoviedb.org](https://www.themoviedb.org/) (email и пароль).  
2. Подтвердите email.  
3. Войдите в аккаунт → Настройки (Settings) → API.  
4. Нажмите "Создать" (Create) для v3 auth.  
5. Скопируйте "API Key (v3 auth)" — это строка вроде "f6b8468192aaf27c05b627a08f755b1d".  
6. Вставьте сюда и нажмите "Сохранить".  
Ключ нужен только для чтения данных — безопасно. Если не ввести, детали придётся заполнять вручную.
""")

# Хранение ключа в сессии
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''

api_input = st.text_input('Ваш API-ключ TMDb', value=st.session_state.api_key, type='password')  # Пароль для скрытия
if st.button('Сохранить ключ'):
    st.session_state.api_key = api_input
    st.success('Ключ сохранён в сессии!')

# Проверка на Streamlit Secrets (твой скрытый ключ по умолчанию)
try:
    default_key = st.secrets["TMDB_API_KEY"]
    if not st.session_state.api_key:
        st.session_state.api_key = default_key
        st.info('Используется ключ по умолчанию из secrets.')
except KeyError:
    pass  # Нет secrets — ок, используем введённый

api_key = st.session_state.api_key

data = load_data()

# Секция добавления/обновления
st.header('Добавить или обновить запись')
category = st.selectbox('Категория', ['Фильм', 'Сериал', 'Мультфильм'])
title = st.text_input('Название')
rating = st.slider('Рейтинг (1-10)', 1, 10, 5)
comment = st.text_area('Комментарий')
parts = st.number_input('Количество частей/сезонов (если API не подтянет)', min_value=1, value=1)

if st.button('Добавить/Обновить'):
    if title:
        is_series = (category == 'Сериал')
        details = get_movie_details(title, api_key, is_series)
        
        entry = {
            'title': title,
            'rating': rating,
            'comment': comment,
            'year': details['year'],
            'genre': details['genre'],
            'parts': parts if parts > 1 else details['parts']  # Приоритет вводу пользователя
        }
        
        key = 'movies' if category == 'Фильм' else 'series' if category == 'Сериал' else 'cartoons'
        # Проверка на обновление
        for i, item in enumerate(data[key]):
            if item['title'].lower() == title.lower():
                data[key][i] = entry
                break
        else:
            data[key].append(entry)
        
        save_data(data)
        st.success(f'Запись "{title}" добавлена/обновлена! Автодетали: Год: {entry["year"]}, Жанр: {entry["genre"]}, Части: {entry["parts"]}')

# Секция просмотра базы
st.header('Твоя база')
for cat, key in [('Фильмы', 'movies'), ('Сериалы', 'series'), ('Мультфильмы', 'cartoons')]:
    st.subheader(cat)
    for item in data[key]:
        st.write(f"**{item['title']}** ({item['year']}, {item['genre']}, Рейтинг: {item['rating']}/10, Части: {item['parts']}) - {item['comment']}")

# Статистика
st.header('Статистика')
total = sum(len(data[k]) for k in data)
avg_rating = sum(sum(i['rating'] for i in data[k]) for k in data) / total if total > 0 else 0
st.write(f'Всего записей: {total}')
st.write(f'Средний рейтинг: {avg_rating:.2f}')

# Рекомендации (простой пример)
st.header('Рекомендации (6 штук)')
recommendations = [
    {'title': 'The Office', 'type': 'Сериал', 'parts': 9, 'reason': 'Комедия, похожа на твои вкусы в юморе.'},
    {'title': 'Inception', 'type': 'Фильм', 'parts': 1, 'reason': 'Фантастика, как Интерстеллар.'},
    {'title': 'Shrek', 'type': 'Мультфильм', 'parts': 4, 'reason': 'Смешной, как твои любимые мульты.'},
    # Ещё 3 — можно динамически генерировать позже
    {'title': 'Rick and Morty', 'type': 'Сериал', 'parts': 6, 'reason': 'Анимация с юмором.'},
    {'title': 'Dune', 'type': 'Фильм', 'parts': 2, 'reason': 'Эпическая фантастика.'},
    {'title': 'Kung Fu Panda', 'type': 'Мультфильм', 'parts': 4, 'reason': 'Приключения и юмор.'},
]
for rec in recommendations:
    st.write(f"**{rec['title']}** ({rec['type']}, {rec['parts']} частей) - {rec['reason']}")

# Удаление
st.header('Удалить запись')
del_title = st.text_input('Название для удаления')
if st.button('Удалить'):
    for key in data:
        data[key] = [i for i in data[key] if i['title'].lower() != del_title.lower()]
    save_data(data)
    st.success(f'"{del_title}" удалено!')