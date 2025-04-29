#Код выполняет поиск недостатков у патентов с сайта яндекс патенты по ключевым словам типо недостатки
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from natasha import Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger, NewsSyntaxParser, Doc

def get_patent_text_selenium(patent_url):
    # Настройка EdgeDriver
    edge_options = Options()
    edge_options.add_argument("--headless")  # Фоновый режим
    driver = webdriver.Edge(options=edge_options)

    try:
        driver.get(patent_url)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'doc-text')))

        soup = BeautifulSoup(driver.page_source, 'html.parser')

    finally:
        driver.quit()

    # Находим все элементы с классом 'doc-text'
    doc_text_divs = soup.find_all('div', class_='doc-text')
    if not doc_text_divs:
        raise Exception("Не удалось найти элементы с классом 'doc-text'.")

    # Извлекаем текст из всех найденных блоков
    full_texts = []
    for div in doc_text_divs:
        paragraphs = div.find_all('p')
        if paragraphs:
            full_texts.append('\n'.join(paragraph.get_text() for paragraph in paragraphs))

    if not full_texts:
        raise Exception("Не удалось извлечь текст из найденных элементов.")

    # Объединяем все тексты в один
    full_text = '\n\n'.join(full_texts)
    print(full_text)
    return full_text

def find_weaknesses(full_text):
    keywords = ['недостаток', 'недостатком', 'недостатки', 'недостатков', 'минусы','недостатками','проблема','проблемой']

    segmenter = Segmenter()
    morph_vocab = MorphVocab()
    emb = NewsEmbedding()
    morph_tagger = NewsMorphTagger(emb)
    syntax_parser = NewsSyntaxParser(emb)

    doc = Doc(full_text)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    doc.parse_syntax(syntax_parser)

    weaknesses = []

    for sentence in doc.sents:
        if any(keyword in sentence.text.lower() for keyword in keywords):
            weaknesses.append(sentence.text)

    return weaknesses

if __name__ == '__main__':
    patent_url = input("Введите URL патента с Яндекс.Патента: ")
    try:
        text = get_patent_text_selenium(patent_url)
        weaknesses = find_weaknesses(text)
        if weaknesses:
            print("Найдены следующие недостатки: ")
            for weakness in weaknesses:
                print(f" - {weakness}")
        else:
            print("Недостатки не найдены")
    except Exception as e:
        print(f"Ошибка: {e}")
