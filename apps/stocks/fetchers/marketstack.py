import requests
from django.conf import settings
from pydantic import BaseModel

from apps.core.fetchers.base import Fetcher


class MarketstackFetcherInput(BaseModel):
    symbol: str


class MarketstackFetcher(Fetcher):
    def fetch_single(self, data: MarketstackFetcherInput) -> tuple[bool, str | float]:
        return self.fetch_multiple({"_": {"symbol": data.symbol}})["_"]

    def fetch_multiple(
        self, data: dict[str, MarketstackFetcherInput]
    ) -> dict[str, tuple[bool, str | float]]:
        symbols = []
        for fetcher, input in data.items():
            symbols.append(input.symbol)

        symbols = ",".join(symbols)
        params = {"access_key": settings.MARKETSTACK_API_KEY}
        url = "http://api.marketstack.com/v1/eod/latest?symbols={}".format(symbols)
        api_result = requests.get(url, params)
        api_response = api_result.json()

        results = {}

        if "error" in api_response:
            for fetcher in data:
                results[fetcher] = (
                    False,
                    (
                        "Could not fetch prices from marketstack: "
                        f"'{api_response['error']['message']}'."
                    ),
                )
            return results

        for fetcher, input in data.items():
            symbol = input.symbol
            results[fetcher] = (False, "Price not found in response.")
            for price in api_response["data"]:
                if price["symbol"] == symbol:
                    results[fetcher] = (True, round(price["close"], 2))
                    break

        return results
