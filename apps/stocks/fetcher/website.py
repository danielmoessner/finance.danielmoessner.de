import re
import time
from bs4 import BeautifulSoup
import requests
from apps.stocks.fetcher.price import save_price
from apps.stocks.models import PriceFetcher, Stock
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


def fetch_price_with_website_fetcher(fetcher: PriceFetcher) -> tuple[bool, str]:
    stock = fetcher.stock
    website = fetcher.data["website"]
    target = fetcher.data["target"]

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
            f"Could not find a price for {stock.ticker} on {website} with {target}.",
        )

    result = re.search("\d{1,5}[.,]\d{2}", str(selection))

    if not result:
        return False, f"Could not find a price inside '{selection}'."

    price = result.group()
    price = price.replace(",", ".")
    price = float(price)
    save_price(price, stock)
    return True, ""


def fetch_prices_with_website_fetchers(
    stocks: list[Stock], messages: list[str] | None = None
):
    i = 0
    for stock in stocks:
        fetchers = list(stock.price_fetchers.filter(type="WEBSITE"))
        for fetcher in fetchers:
            success, message = fetch_price_with_website_fetcher(fetcher)
            if success:
                break
            if messages is not None:
                messages.append(message)
        time.sleep(i)
        i += 1
