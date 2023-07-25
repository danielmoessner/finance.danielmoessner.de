from typing import Callable
from apps.stocks.fetcher.marketstack import (
    MarketstackFetcher,
)
from apps.stocks.fetcher.selenium import (
    SeleniumFetcher,
)
from apps.stocks.fetcher.website import (
    WebsiteFetcher,
)

from apps.stocks.models import PriceFetcher
from datetime import timedelta
from typing import Callable
from django.utils import timezone
from apps.stocks.models import Price, PriceFetcher, Stock
from django.utils import timezone
from apps.stocks.models import Stock
from apps.stocks.forms import PriceForm


def save_price(price: float, stock: Stock) -> None:
    price = PriceForm(
        {
            "ticker": stock.ticker,
            "exchange": stock.exchange,
            "date": timezone.now(),
            "price": price,
        }
    )
    if price.is_valid():
        price.save()


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


def get_fetchers_to_be_run(type: str) -> dict[str, dict[str, int | str]]:
    fetchers_to_be_run = []
    for fetcher in list(PriceFetcher.objects.filter(type=type)):
        if Price.objects.filter(
            ticker=fetcher.stock.ticker, date__gt=timezone.now() - timedelta(days=1)
        ).exists():
            continue
        fetchers_to_be_run.append(fetcher)
    return {str(fetcher.pk): fetcher.data for fetcher in fetchers_to_be_run}


def turn_fetchers_to_data(fetchers: list[PriceFetcher]) -> dict[str, dict]:
    data = {}
    for fetcher in fetchers:
        data[str(fetcher.pk)] = fetcher.data
    return data


def save_prices(results: dict[str, tuple[bool, str | float]]):
    for fetcher, result in results:
        fetcher = PriceFetcher.objects.get(pk=fetcher)
        if result[0]:
            save_price(fetcher.stock, result[1])


FETCHERS: dict[str, FETCHER_FUNCTION] = {
    "WEBSITE": WebsiteFetcher.fetch_single,
    "SELENIUM": SeleniumFetcher.fetch_single,
    "MARKETSTACK": MarketstackFetcher.fetch_single,
}


def fetch_prices():
    fetchers = get_fetchers_to_be_run("WEBSITE")
    results = WebsiteFetcher.fetch_multiple(fetchers)
    save_prices(results)

    fetchers = get_fetchers_to_be_run("SELENIUM")
    results = SeleniumFetcher.fetch_multiple(fetchers)
    save_prices(results)

    fetchers = get_fetchers_to_be_run("MARKETSTACK")
    results = MarketstackFetcher.fetch_multiple(fetchers)
    save_prices(results)
