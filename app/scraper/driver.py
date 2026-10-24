"""Encapsule les opérations Selenium sur Chrome."""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from config import HEADLESS, TIMEOUT

class BrowserDriver:
    def __init__(self):
        options = Options()
        if HEADLESS:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1440,1000")
        options.add_argument("--lang=fr-FR")
        self.browser = webdriver.Chrome(options=options)

    def open(self, url):
        self.browser.get(url)

    def wait_for(self, selector, timeout=TIMEOUT):
        return WebDriverWait(self.browser, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )

    def find_all(self, selector):
        return self.browser.find_elements(By.CSS_SELECTOR, selector)

    def find_in(self, element, selector):
        return element.find_elements(By.CSS_SELECTOR, selector)

    @property
    def body_text(self):
        return self.browser.find_element(By.TAG_NAME, "body").text

    @property
    def page_title(self):
        return self.browser.title

    def close(self):
        self.browser.quit()
