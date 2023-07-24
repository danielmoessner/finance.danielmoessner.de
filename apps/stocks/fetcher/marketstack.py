from django.conf import settings
import requests
from apps.stocks.fetcher.price import save_price
from apps.stocks.models import PriceFetcher, Stock


def fetch_prices_from_marketstack(symbols: list[str]) -> tuple[bool, str]:
    symbols = ",".join(symbols)
    params = {"access_key": settings.MARKETSTACK_API_KEY}
    url = "http://api.marketstack.com/v1/eod/latest?symbols={}".format(symbols)
    api_result = requests.get(url, params)
    api_response = api_result.json()
    if "error" in api_response:
        return (
            False,
            f"Could not fetch prices from marketstack: '{api_response['error']['message']}'.",
        )

    for price in api_response["data"]:
        save_price(
            round(price["close"], 2), Stock.objects.get(ticker=[price["symbol"]])
        )

    return True, ""


def fetch_price_with_marketstack_fetcher(fetcher: PriceFetcher) -> tuple[bool, str]:
    return fetch_prices_from_marketstack([fetcher.data["symbol"]])


def fetch_prices_with_marketstack_fetchers(
    stocks: list[Stock], messages: list[str] | None = None
):
    symbols = []
    for stock in stocks:
        fetcher = stock.price_fetchers.filter(type="MARKETSTACK").first()
        if fetcher is None:
            if messages is not None:
                messages.append(f"Could not find a price fetcher for {stock.ticker}.")
            continue
        symbols.append(fetcher.data["symbol"])

    fetch_prices_from_marketstack(symbols)
