from datetime import timedelta
import re
import time
from typing import Callable
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from .models import Price, PriceFetcher, Stock
from .forms import PriceForm
import requests
import logging


logger = logging.getLogger(__name__)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:113.0) Gecko/20100101 Firefox/98.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
    ":authority:": "api.boerse-frankfurt.de",
    ":method:": "GET",
    ":path:": "/v1/data/quote_box/single?isin=IE00BM67HT60&mic=XETR",
    "X-Security:": "ca60de3ad5356b275e5551b38a21921a",
}

headers = {
    # ":authority:": "api.boerse-frankfurt.de",
    # ":method:": "GET",
    # ":path:": "/v1/data/quote_box/single?isin=IE00BM67HT60&mic=XETR",
    # ":scheme:": "https",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en;q=0.8",
    "Cache-Control": "no-cache",
    "Client-Date": "2023-07-23T14:26:37.677Z",
    "Origin": "https://www.boerse-frankfurt.de",
    "Pragma": "no-cache",
    "Referer": "https://www.boerse-frankfurt.de/",
    "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"99\", \"Brave\";v=\"115\", \"Chromium\";v=\"115\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"macOS\"",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Sec-Gpc": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "X-Client-Traceid": "fe7f571ac7e5d9b3eeec4b46b73b15db",
    "X-Security": "affbfc484bd62698686a06b22e71f33c"
}


def save_price(price: float, stock: Stock) -> None:
    price = PriceForm({'ticker': stock.ticker,
                       'exchange': stock.exchange,
                       'date': timezone.now(),
                       'price': price})
    if price.is_valid():
        price.save()


def get_stocks_to_be_fetched() -> list[Stock]:
    stocks_to_be_fetched = []
    for stock in list(Stock.objects.all()):
        if Price.objects.filter(ticker=stock.ticker, date__gt=timezone.now() - timedelta(days=1)).exists():
            continue
        stocks_to_be_fetched.append(stock)
    return stocks_to_be_fetched


def fetch_prices():
    fetch_prices_with_website_fetchers(get_stocks_to_be_fetched())
    fetch_prices_with_marketstack_fetchers(get_stocks_to_be_fetched())


def fetch_price_with_website_fetcher(fetcher: PriceFetcher) -> tuple[bool, str]:
    stock = fetcher.stock
    website = fetcher.data["website"]
    target = fetcher.data["target"]

    browser = webdriver.Chrome()
    try:
        browser.get(website)
        time.sleep(5)  # wait for the api requests to finish
        html = browser.page_source
    except Exception as e:
        return False, f"An error occured while trying to connect to {website}: {e}."
    finally:
        browser.quit()

    # if r.status_code != 200:
    #     return False, f"Could not connect to {website}. The status code is {r.status_code}."
    
    soup = BeautifulSoup(html, features='html.parser')
    selection = soup.select_one(target)

    if not selection:
        return False, f"Could not find a price for {stock.ticker} on {website} with {target}."

    result = re.search('\d{1,5}[.,]\d{2}', str(selection))
    
    if not result:
        return False, f"Could not find a price inside '{selection}'."
    
    price = result.group()
    price = price.replace(',', '.')
    price = float(price)
    save_price(price, stock)
    return True, ""


def fetch_prices_with_website_fetchers(stocks, messages: list[str] | None=None):
    i = 0
    for stock in stocks:
        fetchers = list(stock.price_fetchers.filter(type="WEBSITE"))
        for fetcher in fetchers:
            success, message = fetch_price_with_website_fetcher(stock, fetcher)
            if success:
                break
            if messages is not None:
                messages.append(message)
        time.sleep(i)
        i += 1



def fetch_prices_from_marketstack(symbols: list[str]) -> tuple[bool, str]:
    symbols = ','.join(symbols)
    params = {
        'access_key': settings.MARKETSTACK_API_KEY
    }
    url = 'http://api.marketstack.com/v1/eod/latest?symbols={}'.format(symbols)    
    api_result = requests.get(url, params)
    api_response = api_result.json()
    if 'error' in api_response:
        return False , f"Could not fetch prices from marketstack: '{api_response['error']['message']}'."
    
    for price in api_response['data']:
        save_price(round(price['close'], 2), Stock.objects.get(ticker=[price['symbol']]))
    
    return True, ""


def fetch_price_with_marketstack_fetcher(fetcher: PriceFetcher) -> tuple[bool, str]:
    return fetch_prices_from_marketstack([fetcher.data["symbol"]])


def fetch_prices_with_marketstack_fetchers(stocks: list[Stock], messages: list[str] | None=None):
    symbols = []
    for stock in stocks:
        fetcher = stock.price_fetchers.filter(type="MARKETSTACK").first()
        if fetcher is None:
            if messages is not None:
                messages.append(f"Could not find a price fetcher for {stock.ticker}.")
            continue
        symbols.append(fetcher.data["symbol"])

    fetch_prices_from_marketstack(symbols)


FETCHER_FUNCTION = Callable[[PriceFetcher], tuple[bool, str]]

FETCHERS: dict[str, FETCHER_FUNCTION] = {
    "WEBSITE": fetch_price_with_website_fetcher,
    "MARKETSTACK": fetch_price_with_marketstack_fetcher,
}
