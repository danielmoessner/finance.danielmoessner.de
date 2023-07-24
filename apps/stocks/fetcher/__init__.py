from typing import Callable
from apps.stocks.fetcher.marketstack import (
    fetch_price_with_marketstack_fetcher,
    fetch_prices_with_marketstack_fetchers,
)
from apps.stocks.fetcher.selenium import (
    fetch_price_with_selenium_fetcher,
    fetch_prices_with_selenium_fetchers,
)
from apps.stocks.fetcher.website import (
    fetch_price_with_website_fetcher,
    fetch_prices_with_website_fetchers,
)

from apps.stocks.models import PriceFetcher
from datetime import timedelta
from typing import Callable
from django.utils import timezone
from apps.stocks.models import Price, PriceFetcher, Stock


FETCHER_FUNCTION = Callable[[PriceFetcher], tuple[bool, str]]


def get_stocks_to_be_fetched() -> list[Stock]:
    stocks_to_be_fetched = []
    for stock in list(Stock.objects.all()):
        if Price.objects.filter(
            ticker=stock.ticker, date__gt=timezone.now() - timedelta(days=1)
        ).exists():
            continue
        stocks_to_be_fetched.append(stock)
    return stocks_to_be_fetched


FETCHERS: dict[str, FETCHER_FUNCTION] = {
    "WEBSITE": fetch_price_with_website_fetcher,
    "SELENIUM": fetch_price_with_selenium_fetcher,
    "MARKETSTACK": fetch_price_with_marketstack_fetcher,
}


def fetch_prices():
    fetch_prices_with_website_fetchers(get_stocks_to_be_fetched())
    fetch_prices_with_selenium_fetchers(get_stocks_to_be_fetched())
    fetch_prices_with_marketstack_fetchers(get_stocks_to_be_fetched())
