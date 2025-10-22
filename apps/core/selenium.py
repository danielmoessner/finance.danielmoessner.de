from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def get_chrome_driver() -> webdriver.Chrome:
    # service = Service(executable_path="/usr/bin/chromedriver")
    service = Service()
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--verbose")
    return webdriver.Chrome(service=service, options=options)
