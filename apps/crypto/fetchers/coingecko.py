import json
from pydantic import BaseModel
import requests
from apps.core.fetchers.base import Fetcher


class CoinGeckoFetcherInput(BaseModel):
    coingecko_id: str


class CoinGeckoFetcher(Fetcher):
    def __fetch(self, ids: list[str]) -> dict[str, float]:
        joined_ids = ','.join(ids)
        url = f'https://api.coingecko.com/api/v3/simple/price?ids={joined_ids}&vs_currencies=eur'
        response = requests.get(url)
        prices = json.loads(response.content.decode())
        results = {}
        for price in prices:
            results[price] = float(prices[price]['eur'])
        return results

    def fetch_single(self, data: CoinGeckoFetcherInput) -> tuple[bool, str | float]:
        results = self.__fetch([data.coingecko_id])
        if data.coingecko_id not in results:
            return False, f"Could not find a price for {data.coingecko_id}."
        return True, results[data.coingecko_id]

    def fetch_multiple(self, data: dict[str, CoinGeckoFetcherInput]) -> dict[str, tuple[bool, str | float]]:
        ids = []
        for _, input in data.items():
            ids.append(input.coingecko_id)
        
        results = self.__fetch(ids)

        for fetcher, input in data.items():
            if input.coingecko_id not in results:
                results[fetcher] = (False, f"Could not find a price for {input.coingecko_id}.")
            else:
                results[fetcher] = (True, results[fetcher])

        return results
