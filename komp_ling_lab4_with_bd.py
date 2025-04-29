import sqlite3
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk import FreqDist, classify, NaiveBayesClassifier
import re, string, random
import pymorphy2

# Инициализация лемматизатора
morph = pymorphy2.MorphAnalyzer()

# Функция для удаления шума
def remove_noise(tokens, stop_words=()):
    cleaned_tokens = []
    for token in tokens:
        token = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', token)
        token = re.sub(r"(@[A-Za-z0-9_]+)", "", token)
        token = morph.parse(token)[0].normal_form  # Лемматизация

        if len(token) > 0 and token not in string.punctuation and token.lower() not in stop_words:
            cleaned_tokens.append(token.lower())
    return cleaned_tokens

# Функция для преобразования токенов в словарь
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

# Классификация с порогом уверенности
def classify_with_threshold(classifier, tokens, threshold=0.7):
    prob_dist = classifier.prob_classify(tokens)
    prob_advantage = prob_dist.prob("Достоинства")
    prob_weakness = prob_dist.prob("Недостатки")

    if prob_advantage > prob_weakness and prob_advantage > threshold:
        return f"Достоинства (вероятность: {prob_advantage:.2f})"
    elif prob_weakness > threshold:
        return f"Недостатки (вероятность: {prob_weakness:.2f})"
    else:
        return "Неопределенно"

if __name__ == "__main__":
    db_path = r"C:\Users\Admin\PycharmProjects\pythonProject23\Diplom_komp_lingvistika\weaknesses.db"

    # Загрузка данных из обеих таблиц
    weakness_texts = load_data_from_db(db_path, "weaknesses")
    advantage_texts = load_data_from_db(db_path, "advantages")

    # Задание стоп-слов
    stop_words = set(stopwords.words('russian'))
    custom_stop_words = {"например", "также", "который", "это", "которые","данный"}
    stop_words.update(custom_stop_words)

    # Очистка и токенизация
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

    # Точность
    accuracy = classify.accuracy(classifier, test_data)
    print(f"Точность модели: {accuracy * 100:.2f}%")

    # Информативные признаки
    print("Наиболее информативные признаки:")
    classifier.show_most_informative_features(100)

    # Тестовые примеры
    test_texts = [
    "Эта система позволяет снизить количество ошибок при обработке данных.",
    "Этот способ уменьшает время на выполнение операции.",
    "Данный алгоритм ускоряет процесс анализа данных.",
    "Данный алгоритм оптимизирует вычисления, сокращая время обработки."
    ]

    for text in test_texts:
        custom_tokens = remove_noise(word_tokenize(text), stop_words)
        prediction = classify_with_threshold(classifier, dict([token, True] for token in custom_tokens), threshold=0.5)
        print(f"Текст: {text}")
        print(f"Классификация: {prediction}")
        print("-" * 50)
print("\n--- Статистика данных ---")
print(f"Текстов с недостатками: {len(weakness_texts)}")
print(f"Текстов с достоинствами: {len(advantage_texts)}")
print(f"Всего данных: {len(weakness_texts) + len(advantage_texts)}")
print(f"Обучающая выборка (train_data): {len(train_data)} примеров")
print(f"Тестовая выборка (test_data): {len(test_data)} примеров")