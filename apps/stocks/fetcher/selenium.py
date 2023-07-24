import re
import time
from bs4 import BeautifulSoup
from apps.core.selenium import get_chrome_driver
from apps.stocks.fetcher.price import save_price
from apps.stocks.models import PriceFetcher, Stock


def fetch_price_with_selenium_fetcher(fetcher: PriceFetcher) -> tuple[bool, str]:
    stock = fetcher.stock
    website = fetcher.data["website"]
    target = fetcher.data["target"]

    browser = get_chrome_driver()
    try:
        browser.get(website)
        time.sleep(5)  # wait for the api requests to finish
        html = browser.page_source
    except Exception as e:
        return False, f"An error occured while trying to connect to {website}: {e}."
    finally:
        browser.quit()

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


def fetch_prices_with_selenium_fetchers(
    stocks: list[Stock], messages: list[str] | None = None
):
    i = 0
    for stock in stocks:
        fetchers = list(stock.price_fetchers.filter(type="SELENIUM"))
        for fetcher in fetchers:
            success, message = fetch_price_with_selenium_fetcher(fetcher)
            if success:
                break
            if messages is not None:
                messages.append(message)
        time.sleep(i)
        i += 1
