import sqlite3
import clickhouse_connect
import re

# Подключение к ClickHouse
client1 = clickhouse_connect.get_client(
    host='localhost',
    port=8123,
    username='dev',
    password='dev',
    database='dev'
)

# Подключение к SQLite
sqlite_conn = sqlite3.connect('patents2.db')
sqlite_cursor = sqlite_conn.cursor()

# Создание таблиц, если их нет
sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS advantages (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          text TEXT)''')

sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS weaknesses (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          text TEXT)''')

sqlite_conn.commit()

# Ключевые слова
advantages_keywords = [
    "эффективный", "улучшенный", "надёжный", "высокая точность", "технический результат",
    "технической задачей", "позволяет", "достигается", "улучшает", "повышает"
]

weaknesses_keywords = [
    "сложность", "дороговизна", "низкая эффективность", "ограничение", 'недостаток',
    'недостатком', 'недостатки', 'недостатков', 'минусы', 'недостатками', 'проблема', 'проблемой'
]

stop_words = ["опубл"]

# Получение текстов патентов из ClickHouse
patents = client1.query(
    "SELECT description FROM patent_google WHERE inventorOrAuthor != 'Виталий Павлович Панкратов'"
).result_rows


# Функция для парсинга списков или обычного текста
def extract_list_items_or_sentences(text):
    # Ищем списки вида:
    # 1. текст
    # 2. текст
    matches = re.findall(r'\n\d+\.\s*(.*?)(?=(?:\n\d+\.|$))', text, flags=re.DOTALL)

    if matches:
        return [m.strip() for m in matches]

    # Если нет списка — обычное разбиение на предложения
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    return [sentence.strip() for sentence in sentences]


for (text,) in patents:  # Распаковываем кортеж

    if text is None:
        continue

    sentences = extract_list_items_or_sentences(text)

    for sentence in sentences:

        sentence_lower = sentence.lower()

        if any(stop_word in sentence_lower for stop_word in stop_words):
            continue

        found_advantages = [kw for kw in advantages_keywords if kw in sentence_lower and kw not in stop_words]
        found_weaknesses = [kw for kw in weaknesses_keywords if kw in sentence_lower and kw not in stop_words]

        if found_advantages:
            sqlite_cursor.execute("INSERT INTO advantages (text) VALUES (?)", (sentence,))

        if found_weaknesses:
            sqlite_cursor.execute("INSERT INTO weaknesses (text) VALUES (?)", (sentence,))

sqlite_conn.commit()
sqlite_conn.close()
client1.close()
