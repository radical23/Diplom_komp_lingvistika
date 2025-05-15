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
sqlite_conn = sqlite3.connect('patents4.db')
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
advantages_keywords = ["эффективный", "улучшенный", "надёжный", "высокая точность", "технический результат",
                       "технической задачей", "позволяет", "достигается", "улучшает", "повышает"]
weaknesses_keywords = ["сложность", "дороговизна", "низкая эффективность", "ограничение", 'недостаток','проблемам',
                       'недостатком', 'недостатки', 'недостатков', 'минусы', 'недостатками', 'проблема', 'проблемой','не обеспечивает','не обеспечивают','техническая проблема']
stop_words = [
    "опубл",
    re.compile(r'\b\d{1,2}\.\d{1,2}\.\d{4}\b'),  # dd.mm.yyyy
    re.compile(r'\b\d{4}-\d{1,2}-\d{1,2}\b'),    # yyyy-mm-dd
    re.compile(r'\b\d{1,2}/\d{1,2}/\d{4}\b')     # mm/dd/yyyy
]
# Получение текстов патентов из ClickHouse
patents = client1.query("SELECT description FROM patent_google WHERE inventorOrAuthor != 'Виталий Павлович Панкратов'").result_rows

# Функция проверки на стоп-слова с учетом регулярных выражений
def contains_stop_word(text):
    text_lower = text.lower()
    for item in stop_words:
        if isinstance(item, re.Pattern):
            if item.search(text):  # Проверка по регулярному выражению
                return True
        elif item in text_lower:  # Проверка обычных стоп-слов
            return True
    return False

# Функция для разделения текста на предложения
def split_text_into_sentences(text):
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    return [sentence.strip() for sentence in sentences]

for (text,) in patents:  # Распаковываем кортеж
    if text is None:
        continue

    sentences = split_text_into_sentences(text)

    for sentence in sentences:
        if contains_stop_word(sentence):
            continue

        sentence_lower = sentence.lower()

        found_advantages = [kw for kw in advantages_keywords if kw in sentence_lower]
        found_weaknesses = [kw for kw in weaknesses_keywords if kw in sentence_lower]

        if found_advantages:
            sqlite_cursor.execute("INSERT INTO advantages (text) VALUES (?)", (sentence,))

        if found_weaknesses:
            sqlite_cursor.execute("INSERT INTO weaknesses (text) VALUES (?)", (sentence,))

sqlite_conn.commit()
sqlite_conn.close()
client1.close()