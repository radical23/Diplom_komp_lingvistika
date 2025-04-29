import re
import string
import pickle
from nltk.tokenize import word_tokenize
from nltk import classify
from razdel import sentenize
import pymorphy2

# Инициализация лемматизатора
morph = pymorphy2.MorphAnalyzer()

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

def get_tokens_for_model(tokens_list):
    for tokens in tokens_list:
        yield dict([token, True] for token in tokens)

stop_phrases = [
    'опубл', 'патент', 'прототип', 'описан', 'известен', 'зарегистрирован',
    'авторское свидетельство', 'аналог',
]

def contains_stop_phrases(sentence, stop_phrases):
    return any(stop_word in sentence.lower() for stop_word in stop_phrases)

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

def extract_referenced_patents(text):
    patent_pattern = r"(?i)\b(?:RU|CN|US|DE|РФ|SK|EP|JP|SU|WO)\s*\d{5,}\b|(?:№|#|N)\s*\d{5,}\b"
    return re.findall(patent_pattern, text)

def classify_weakness_by_patent(document, classifier, stop_words, threshold=0.5):
    sentences = [sent.text for sent in sentenize(document)]
    results = []
    current_patents = []

    for sentence in sentences:
        patents_in_sentence = extract_referenced_patents(sentence)

        if patents_in_sentence:
            current_patents = patents_in_sentence

        if not current_patents:
            continue

        if contains_stop_phrases(sentence, stop_phrases):
            continue

        tokens = remove_noise(word_tokenize(sentence), stop_words)
        tokens_dict = dict([token, True] for token in tokens)
        classification = classify_with_threshold(classifier, tokens_dict, threshold)

        if "Недостатки" in classification:
            for pat in current_patents:
                results.append({
                    "патент": pat,
                    "предложение": sentence,
                    "классификация": classification
                })

    return results

def load_classifier(path="classifier.pickle"):
    with open(path, "rb") as f:
        classifier = pickle.load(f)
    return classifier
