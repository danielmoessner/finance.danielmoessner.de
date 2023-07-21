from datetime import timedelta
import re
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone

from .models import Price, Stock
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
    fetch_prices_with_website(get_stocks_to_be_fetched())
    fetch_prices_with_marketstack(get_stocks_to_be_fetched())


def fetch_prices_with_website(stocks, messages: list[str] | None=None):
    for stock in stocks:
        fetcher = stock.price_fetchers.filter(type="WEBSITE").first()
        if fetcher is None:
            if messages is not None:
                messages.append(f"Could not find a price fetcher for {stock.ticker}.")
            continue

        website = fetcher.data["website"]
        target = fetcher.data["target"]
        try:
            r = requests.get(website, headers=headers)
        except requests.exceptions.ConnectionError:
            if messages is not None:
                messages.append(f"Could not connect to {website}.")
            continue

        if r.status_code != 200:
            if messages is not None:
                messages.append(f"Could not connect to {website}. The status code is {r.status_code}.")
            continue
        
        text = r.text
        soup = BeautifulSoup(text, features='html.parser')
        selection = soup.select_one(target)
        
        if not selection:
            if messages is not None:
                messages.append(f"Could not find a price for {stock.ticker} on {website} with {target}.")
            continue

        price = re.search('[0-9]+,[0-9]+', str(selection)).group()
        price = price.replace(',', '.')
        price = float(price)
        save_price(price, stock)  


def fetch_prices_with_marketstack(stocks: list[Stock], messages: list[str] | None=None):
    stocks_as_dict = {stock.ticker: stock for stock in stocks}

    symbols = []
    for stock in stocks:
        fetcher = stock.price_fetchers.filter(type="MARKETSTACK").first()
        if fetcher is None:
            if messages is not None:
                messages.append(f"Could not find a price fetcher for {stock.ticker}.")
            continue
        symbols.append(fetcher.data["symbol"])

    symbols = ','.join(symbols)
    params = {
        'access_key': settings.MARKETSTACK_API_KEY
    }
    url = 'http://api.marketstack.com/v1/eod/latest?symbols={}'.format(symbols)    
    api_result = requests.get(url, params)
    api_response = api_result.json()
    if 'error' in api_response:
        if messages is not None:
            messages.append(f"Could not fetch prices from marketstack: '{api_response['error']['message']}'.")
        return
    
    for price in api_response['data']:
        save_price(round(price['close'], 2), stocks_as_dict[price['symbol']])


FETCHERS = {
    "WEBSITE": fetch_prices_with_website,
    "MARKETSTACK": fetch_prices_with_marketstack,
}
