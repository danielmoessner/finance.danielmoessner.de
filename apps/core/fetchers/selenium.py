import re
import time

from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl

from apps.core.fetchers.base import Fetcher
from apps.core.selenium import get_chrome_driver


class SeleniumFetcherInput(BaseModel):
    website: HttpUrl
    target: str


class SeleniumFetcher(Fetcher):
    def fetch_single(self, data: SeleniumFetcherInput) -> tuple[bool, str | float]:
        browser = get_chrome_driver()
        try:
            browser.get(str(data.website))
            time.sleep(5)  # wait for the api requests to finish
            html = browser.page_source
        except Exception as e:
            return (
                False,
                f"An error occured while trying to connect to {data.website}: {e}.",
            )
        finally:
            browser.quit()

        soup = BeautifulSoup(html, features="html.parser")
        selection = soup.select_one(data.target)

        if not selection:
            return (
                False,
                f"Could not find a price for on {data.website} with {data.target}.",
            )

        result = re.search("\d{1,5}[.,]\d{2}", str(selection))

        if not result:
            return False, f"Could not find a price inside '{selection}'."

        price = result.group()
        price = price.replace(",", ".")
        price = float(price)
        return True, price

    def fetch_multiple(
        self, data: dict[str, SeleniumFetcherInput]
    ) -> dict[str, tuple[bool, str | float]]:
        results = {}
        for fetcher, input in data.items():
            result = self.fetch_single(input)
            results[fetcher] = result
        return results
