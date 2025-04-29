"""
Этот код парсит description с сайта google patents и выводит его
P.S. сделать такое же описание только для yandex патенты
p.p.s. данный код нужен для того чтобы человек загружал текст патента по ссылке в будущем веб приложении и считанное описание проверялось
нейронкой на наличие в нем недостатков описанных внутри патентов!
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def fetch_patent_description_selenium(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # без открытия окна браузера

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    time.sleep(5)  # ждем, пока страница загрузится

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    description_section = soup.find("section", {"id": "description"})

    if not description_section:
        print("Описание не найдено.")
        return ""

    return description_section.get_text(separator="\n", strip=True)

url = input("Вставь ссылку на патент: ")

#url = "https://patents.google.com/patent/RU2669005C2/ru?q=(%D0%B2%D0%B8%D0%B4%D0%B5%D0%BE%D0%BA%D0%B0%D1%80%D1%82%D0%B0)&oq=%D0%B2%D0%B8%D0%B4%D0%B5%D0%BE%D0%BA%D0%B0%D1%80%D1%82%D0%B0"
patent_text = fetch_patent_description_selenium(url)
print(patent_text)
