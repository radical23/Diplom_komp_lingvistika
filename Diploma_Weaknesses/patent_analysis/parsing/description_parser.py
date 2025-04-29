from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

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
        return "Описание не найдено."
        
    
    return description_section.get_text(separator="\n",strip=None)