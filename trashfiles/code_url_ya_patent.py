from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def get_patent_html(patent_url):
    # Настройка EdgeDriver
    edge_options = Options()
    edge_options.add_argument("--headless")  # Фоновый режим
    driver = webdriver.Edge(options=edge_options)

    try:
        driver.get(patent_url)
        # Ожидаем, пока загрузится основной элемент на странице
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'doc-text')))

        # Извлекаем HTML
        page_source = driver.page_source

    finally:
        driver.quit()

    return page_source

if __name__ == '__main__':
    patent_url = input("Введите URL патента с Яндекс.Патента: ")
    try:
        # Получаем HTML страницы
        html_content = get_patent_html(patent_url)

        # Используем BeautifulSoup для форматирования HTML
        formatted_html = BeautifulSoup(html_content, 'html.parser').prettify()

        # Печатаем отформатированный HTML
        print(formatted_html)

        # Также сохраняем HTML в файл
        with open("patent_page.html", "w", encoding="utf-8") as file:
            file.write(formatted_html)

        print("HTML страницы сохранен в файл 'patent_page.html'.")

    except Exception as e:
        print(f"Ошибка: {e}")
