import streamlit as st
import json
from tmdbv3api import TMDb, Movie, TV

# Настройка TMDB API
tmdb = TMDb()
tmdb.api_key = 'YOUR_API_KEY'  # Вставь свой TMDB API-ключ здесь!
tmdb.language = 'ru'
movie_api = Movie()
tv_api = TV()

# Файл базы
DB_FILE = 'movie_database.json'

# Загрузка/сохранение
@st.cache_data
def load_db():
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'items': []}

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)
    st.warning("Изменения сохранены. Для постоянного хранения — commit в GitHub!")

# Автодополнение через TMDB
def fetch_details(title, is_series=False):
    try:
        if is_series:
            result = tv_api.search(title)
        else:
            result = movie_api.search(title)
        if result:
            first = result[0]
            year = first.get('first_air_date', 'Неизвестно')[:4] if is_series else first.get('release_date', 'Неизвестно')[:4]
            genres = first.get('genre_ids', [])
            genre_str = 'Фантастика' if 878 in genres else 'Комедия' if 35 in genres else 'Неизвестно'  # Упрощённо
            return year, genre_str
    except:
        pass
    return 'Неизвестно', 'Неизвестно'

# Основное приложение
st.title("MovieTracker - Твой КиноАрхив")

db = load_db()
items = db['items']

# Sidebar
action = st.sidebar.selectbox("Действие", ["Просмотр списка", "Добавление", "Обновление/Удаление", "Статистика", "Рекомендации", "Поиск"])

if action == "Просмотр списка":
    st.subheader("Твой список (отсортировано по рейтингу)")
    if items:
        sorted_items = sorted(items, key=lambda x: float(x['rating']) if x['rating'].isdigit() else 0, reverse=True)
        for item in sorted_items:
            st.write(f"**{item['type']}: {item['name']}** ({item['year']}, {item['genre']}, Рейтинг: {item['rating']}, Комментарий: {item['comment']})")
    else:
        st.write("База пуста.")

elif action == "Добавление":
    st.subheader("Добавьте фильм или сериал")
    item_type = st.selectbox("Тип", ["Фильм", "Сериал"])
    name = st.text_input("Название")
    rating = st.number_input("Рейтинг (1-10)", min_value=1, max_value=10, value=5)
    comment = st.text_area("Комментарий")
    if st.button("Добавить"):
        if name:
            is_series = item_type == "Сериал"
            year, genre = fetch_details(name, is_series)
            new_item = {
                'type': item_type,
                'name': name,
                'year': year,
                'genre': genre,
                'rating': str(rating),
                'comment': comment
            }
            items.append(new_item)
            save_db({'items': items})
            st.success(f"Добавлено: {item_type} '{name}'")
            st.experimental_rerun()

elif action == "Обновление/Удаление":
    st.subheader("Обновите или удалите")
    names = [i['name'] for i in items]
    selected = st.selectbox("Элемент", names)
    if selected:
        item = next(i for i in items if i['name'] == selected)
        new_rating = st.number_input("Новый рейтинг", min_value=1, max_value=10, value=int(item['rating']) if item['rating'].isdigit() else 5)
        new_comment = st.text_area("Новый комментарий", item['comment'])
        if st.button("Обновить"):
            item['rating'] = str(new_rating)
            item['comment'] = new_comment
            save_db({'items': items})
            st.success("Обновлено!")
            st.experimental_rerun()
        if st.button("Удалить"):
            items.remove(item)
            save_db({'items': items})
            st.success("Удалено!")
            st.experimental_rerun()

elif action == "Статистика":
    st.subheader("Статистика")
    total = len(items)
    ratings = [float(i['rating']) for i in items if i['rating'].isdigit()]
    avg = sum(ratings) / len(ratings) if ratings else 0
    genres = {}
    for i in items:
        g = i['genre']
        genres[g] = genres.get(g, 0) + 1
    top_genre = max(genres, key=genres.get) if genres else 'Нет'
    st.write(f"Всего: {total}")
    st.write(f"Средний рейтинг: {avg:.1f}")
    st.write(f"Топ-жанр: {top_genre} ({genres[top_genre]})")

elif action == "Рекомендации":
    st.subheader("Рекомендации")
    genres = {}
    for i in items:
        g = i['genre']
        genres[g] = genres.get(g, 0) + 1
    top_genre = max(genres, key=genres.get) if genres else 'Неизвестно'
    st.write(f"На основе топ-жанра '{top_genre}': Попробуй фильмы вроде 'Example Movie' в этом жанре!")

elif action == "Поиск":
    st.subheader("Поиск")
    query = st.text_input("Введите название или жанр")
    if query:
        results = [i for i in items if query.lower() in i['name'].lower() or query.lower() in i['genre'].lower()]
        for item in results:
            st.write(f"**{item['type']}: {item['name']}** ({item['year']}, {item['genre']}, {item['rating']}, {item['comment']})")