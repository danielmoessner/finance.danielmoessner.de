from typing import Callable, Mapping

from pydantic import BaseModel

from apps.core.fetchers.selenium import SeleniumFetcher
from apps.core.fetchers.website import WebsiteFetcher
from apps.stocks.fetchers.marketstack import MarketstackFetcher
from apps.stocks.models import Price, PriceFetcher

FETCHER_FUNCTION = Callable[[PriceFetcher], tuple[bool, str]]


def get_fetchers_to_be_run(fetcher_type: str) -> dict[str, BaseModel]:
    fetchers_to_be_run: list[PriceFetcher] = []
    for fetcher in list(PriceFetcher.objects.filter(fetcher_type=fetcher_type)):
        price = (
            Price.objects.filter(ticker=fetcher.stock.ticker).order_by("-date").first()
        )
        if price and not price.is_old:
            continue
        fetchers_to_be_run.append(fetcher)
    return {str(fetcher.pk): fetcher.fetcher_input for fetcher in fetchers_to_be_run}


def save_prices(results: Mapping[str, tuple[bool, str | float]]):
    for fetcher, result in results.items():
        fetcher = PriceFetcher.objects.get(pk=fetcher)
        if result[0]:
            assert isinstance(result[1], float)
            fetcher.save_price(result[1])
        else:
            assert isinstance(result[1], str)
            fetcher.set_error(result[1])


def fetch_prices():
    data = get_fetchers_to_be_run("WEBSITE")
    results = WebsiteFetcher().fetch_multiple(data)
    save_prices(results)

    data = get_fetchers_to_be_run("SELENIUM")
    results = SeleniumFetcher().fetch_multiple(data)
    save_prices(results)

    data = get_fetchers_to_be_run("MARKETSTACK")
    results = MarketstackFetcher().fetch_multiple(data)
    save_prices(results)
