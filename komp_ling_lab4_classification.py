import sqlite3
import pickle
import psycopg2
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk import FreqDist, classify, NaiveBayesClassifier, bigrams, trigrams
import re, string, random
import pymorphy2
from razdel import sentenize

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# Инициализация лемматизатора
morph = pymorphy2.MorphAnalyzer()

def connect_postgres():
    conn = psycopg2.connect(
        dbname = "postgres",
        user="postgres",
        password="123456",
        host="localhost",
        port="5434"
    )
    return conn

def create_table_if_not_exists(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS classified_weaknesses (
                id SERIAL PRIMARY KEY,
                patent VARCHAR(255),
                sentence TEXT,
                classification VARCHAR(100)
            );
        """)
        conn.commit()

# Функция для удаления шума и формирования биграмм/триграмм
def remove_noise(tokens, stop_words=()):
    cleaned_tokens = []
    for token in tokens:
        token = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', token)
        token = re.sub(r"(@[A-Za-z0-9_]+)", "", token)
        token = morph.parse(token)[0].normal_form  # Лемматизация

        if len(token) > 0 and token not in string.punctuation and token.lower() not in stop_words:
            cleaned_tokens.append(token.lower())

    # # Формирование биграмм и триграмм
    # bigram_list = list(bigrams(cleaned_tokens))
    # trigram_list = list(trigrams(cleaned_tokens))

    # # Преобразуем их в строковый формат для удобства
    # bigram_list = ["_".join(b) for b in bigram_list]
    # trigram_list = ["_".join(t) for t in trigram_list]

    # Объединяем все токены
    return cleaned_tokens 

def fetch_patent_description_selenium(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
    driver.get(url)

    time.sleep(5)

    soup =BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    description_section = soup.find("section",{"id":"description"})

    if not description_section:
        print("Описание не найдено.")
        return ""
    
    return description_section.get_text(separator="\n",strip=None)

# Функция для преобразования токенов в словарь признаков
def get_tokens_for_model(tokens_list):
    for tokens in tokens_list:
        yield dict([token, True] for token in tokens)

# Функция загрузки данных из таблицы
def load_data_from_db(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT text FROM {table_name}")
    data = cursor.fetchall()
    conn.close()
    return [item[0] for item in data]

stop_phrases = [
    'опубл', 
    'патент', 
    'прототип', 
    'описан', 
    'известен', 
    'зарегистрирован',
    'авторское свидетельство',
    'аналог',
]

def contains_stop_phrases(sentence, stop_phrases):
    return any(stop_word in sentence.lower() for stop_word in stop_phrases)

# Классификация с порогом уверенности
def classify_with_threshold(classifier, tokens, threshold=0.5):
    prob_dist = classifier.prob_classify(tokens)
    prob_advantage = prob_dist.prob("Достоинства")
    prob_weakness = prob_dist.prob("Недостатки")

    if prob_advantage > prob_weakness and prob_advantage > threshold:
        return f"Достоинства (вероятность: {prob_advantage:.2f})"
    elif prob_weakness > threshold:
        return f"Недостатки (вероятность: {prob_weakness:.2f})"
    else:
        return "Неопределенно"

def classify_patent_document(document,classifier,tokens,threshold=0.5):
    sentences = [sent.text for sent in sentenize(document)]
    results = []

    for sentence in sentences:

        if contains_stop_phrases(sentence, stop_phrases):
            continue
        
        tokens = remove_noise(word_tokenize(sentence),stop_words)
        tokens_dict = dict([token,True] for token in tokens)
        classification = classify_with_threshold(classifier,tokens_dict,threshold)

        if "Недостатки" in classification:
            results.append((sentence,classification))
    
    return results

def extract_referenced_patents(text):
    # Простой регэксп для патентов типа US 1234567 B2
    patent_pattern = r"(?i)\b(?:RU|CN|US|DE|РФ|SK|EP|JP|SU|WO)\s*\d{5,}\b|(?:№|#|N)\s*\d{5,}\b"
    return re.findall(patent_pattern, text)

        
def classify_weakness_by_patent(document, classifier, stop_words, threshold=0.5):
    sentences = [sent.text for sent in sentenize(document)]
    results = []
    current_patents = []

    for sentence in sentences:
        patents_in_sentence = extract_referenced_patents(sentence)

        if patents_in_sentence:
            current_patents = patents_in_sentence  # Обновляем текущий патент по ходу текста

        if not current_patents:
            continue  # Пропускаем предложения без ссылок на патенты

        if contains_stop_phrases(sentence, stop_phrases):
            continue

        tokens = remove_noise(word_tokenize(sentence), stop_words)
        tokens_dict = dict([token, True] for token in tokens)
        classification = classify_with_threshold(classifier, tokens_dict, threshold)

        if "Недостатки" in classification:
            # Связываем недостаток с каждым упомянутым патентом
            for pat in current_patents:
                results.append({
                    "патент": pat,
                    "предложение": sentence,
                    "классификация": classification
                })

    return results

def save_weaknesses_to_postgres(results,conn):
    try:   
        with conn.cursor() as cur:
            print(f"Попытка сохранить {len(results)} записей в PostgreSQL")
            for item in results:
                print(f"Сохранение: {item}")
                cur.execute("""
                    INSERT INTO classified_weaknesses (patent, sentence, classification)
                    VALUES (%s, %s, %s);
                    """, (item["патент"], item["предложение"], item["классификация"]))
            conn.commit()
            print("Данные успешно сохранены в PostgreSQL")  # Отладочное сообщение
    except Exception as e:
        print(f"Ошибка при сохранении в PostgreSQL: {e}")  # Отладочное сообщение
        conn.rollback()

if __name__ == "__main__":
    #db_path = r"C:\Users\Admin\PycharmProjects\pythonProject23\Diplom_komp_lingvistika\patents.db"
    db_path = r"C:\Users\Admin\PycharmProjects\pythonProject23\Diplom_komp_lingvistika\patents4.db"
    # Загрузка данных из обеих таблиц
    weakness_texts = load_data_from_db(db_path, "weaknesses")
    advantage_texts = load_data_from_db(db_path, "advantages")

    # Задание стоп-слов
    stop_words = set(stopwords.words('russian'))
    custom_stop_words = {"например", "также", "который", "это", "которые","данный","опубл."}
    stop_words.update(custom_stop_words)

    # Очистка и токенизация с биграммами и триграммами
    weakness_tokens_list = [remove_noise(word_tokenize(text), stop_words) for text in weakness_texts]
    advantage_tokens_list = [remove_noise(word_tokenize(text), stop_words) for text in advantage_texts]

    # Формирование данных для модели
    weakness_tokens_for_model = list(get_tokens_for_model(weakness_tokens_list))
    advantage_tokens_for_model = list(get_tokens_for_model(advantage_tokens_list))

    # Создание датасета
    dataset = ([(tokens, "Недостатки") for tokens in weakness_tokens_for_model] +
               [(tokens, "Достоинства") for tokens in advantage_tokens_for_model])

    # Перемешивание
    random.shuffle(dataset)

    # Разделение на обучение и тест
    train_data = dataset[:int(0.8 * len(dataset))]
    test_data = dataset[int(0.8 * len(dataset)):]

    # Обучение модели
    classifier = NaiveBayesClassifier.train(train_data)

    
    # import pickle
    # with open("classifier.pickle", "wb") as f:
    #     pickle.dump(classifier, f)
# --------------------------------

    # Точность
    accuracy = classify.accuracy(classifier, test_data)
    print(f"Точность модели: {accuracy * 100:.2f}%")

    # Информативные признаки
    print("Наиболее информативные признаки:")
    classifier.show_most_informative_features(100)

    url = input("Вставь ссылку на патент: ")

    patent_text = fetch_patent_description_selenium(url)
    print(patent_text)

    classified_weaknesses = classify_weakness_by_patent(patent_text, classifier, stop_words)
# Тестовые примеры
    # test_texts = [
    #             "Область техники, к которой относится изобретение настоящее изобретение относится к креслу-коляске, обеспечивающему возможность стояния. Уровень техники По меньшей мере 6 миллионов человек во всем мире нуждаются в долгосрочном или постоянном использовании кресла-коляски вследствие утраты функциональности нижних конечностей. Утрата функциональности нижних конечностей может быть вызвана такими состояниями, как повреждение спинного мозга (ПСМ), травматическое повреждение головного мозга (ТПГМ), инсульт, церебральный паралич (ЦП), спинальный дизрафизм, множественный склероз (МС) и др. Длительное пребывание в положении сидя в кресле-коляске может вызвать физиологическое или психологическое истощение или способствовать ему. Результатом такого истощения может быть неудовлетворительное состояние здоровья, плохое качество жизни, низкая самооценка и высокие расходы на медицинское обслуживание. Кроме того, сидение в кресле-коляске может оказывать негативное влияние или препятствовать социальному взаимодействию с лицами, имеющими возможность стоять. Имеются описания кресел-колясок, позволяющих пользователю стоять. Различные конфигурации таких описанных кресел-колясок служат для разных целей. Некоторые из них позволяют пользователю стоять во время ограниченного движения кресла-коляски. Однако такие описанные кресла-коляски наиболее эффективны в движении, когда пользователь находится в положении сидя. Устойчивое движение кресла-коляски, когда пользователь стоит, может быть ограничено, например, относительно медленным движением по горизонтальным поверхностям."  
    # ]

    # for text in test_texts:
    #     custom_tokens = remove_noise(word_tokenize(text), stop_words)
    #     prediction = classify_with_threshold(classifier, dict([token, True] for token in custom_tokens), threshold=0.5)
    #     print(f"Текст: {text}")
    #     print(f"Классификация: {prediction}")
    #     print("-" * 50)
    print("Выявленные недостатки:")
    for item in classified_weaknesses:
        print(f"\nПатент: {item['патент']}")
        print(f"Предложение: {item['предложение']}")
        print(f"Классификация: {item['классификация']}")


    print("\n--- Статистика данных ---")
    print(f"Текстов с недостатками: {len(weakness_texts)}")
    print(f"Текстов с достоинствами: {len(advantage_texts)}")
    print(f"Всего данных: {len(weakness_texts) + len(advantage_texts)}")
    print(f"Обучающая выборка (train_data): {len(train_data)} примеров")
    print(f"Тестовая выборка (test_data): {len(test_data)} примеров")

    if classified_weaknesses:
        conn_pg = connect_postgres()
        create_table_if_not_exists(conn_pg)
        save_weaknesses_to_postgres(classified_weaknesses, conn_pg)
        conn_pg.close()
    else:
        print("Нет данных для сохранения в PostgreSQL")
    