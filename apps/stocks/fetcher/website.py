import re
import time
from bs4 import BeautifulSoup
import requests
from apps.stocks.fetcher.base import Fetcher


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


class WebsiteFetcher(Fetcher):
    def fetch_single(self, website: str, target: str) -> tuple[bool, str | float]:
        try:
            resp = requests.get(website, headers=headers)
            html = resp.text
        except Exception as e:
            return False, f"An error occured while trying to connect to {website}: {e}."

        if resp.status_code != 200:
            return (
                False,
                f"Could not connect to {website}. The status code is {resp.status_code}.",
            )

        soup = BeautifulSoup(html, features="html.parser")
        selection = soup.select_one(target)

        if not selection:
            return (
                False,
                f"Could not find a price on {website} with {target}.",
            )

        result = re.search("\d{1,5}[.,]\d{2}", str(selection))

        if not result:
            return False, f"Could not find a price inside '{selection}'."

        price = result.group()
        price = price.replace(",", ".")
        price = float(price)
        return True, price

    def fetch_multiple(
        self, data: dict[str, dict[str, str | int]]
    ) -> dict[str, tuple[bool, str | float]]:
        i = 0
        results = {}
        for fetcher, input in data.items():
            result = self.fetch_single(**input)
            results[fetcher] = result
            time.sleep(i)
            i += 1
        return results
