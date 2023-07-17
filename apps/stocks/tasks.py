from datetime import timedelta
from django.conf import settings
from django.utils import timezone

from .models import Price, Stock
from .forms import PriceForm
import requests
import logging


logger = logging.getLogger(__name__)


def fetch_prices():
    price_fetcher_stocks = []
    marketstack_stocks = []
    for stock in list(Stock.objects.all()):
        if Price.objects.filter(ticker=stock.ticker, date__gt=timezone.now() - timedelta(days=1)).exists():
            continue
        if hasattr(stock, 'price_fetcher'):
            price_fetcher_stocks.append(stock)
        else:
            marketstack_stocks.append(stock)
    fetch_prices_with_price_fetchers(price_fetcher_stocks)
    fetch_prices_from_marketstack(marketstack_stocks)


def fetch_prices_with_price_fetchers(stocks):
    for stock in stocks:
        fetched_price = stock.price_fetcher.get_price()
        if fetched_price:
            price = PriceForm({'ticker': stock.ticker,
                               'exchange': stock.exchange,
                               'date': timezone.now(),
                               'price': fetched_price})
            if price.is_valid():
                price.save()
        else:
            message = 'I could not fetch a price for this stock: {}. I tried to use the price fetcher.'.format(stock)
            logger.info(message)


def fetch_prices_from_marketstack(stocks):
    # create a list of all symbols for the query
    symbols = [stock.get_marketstack_symbol() for stock in stocks]
    symbols = set(symbols)
    symbols = ','.join(symbols)
    # set the necessary data for the query
    params = {
        'access_key': settings.MARKETSTACK_API_KEY
    }
    url = 'http://api.marketstack.com/v1/eod/latest?symbols={}'.format(symbols)
    # fetch the data
    try:
        api_result = requests.get(url, params)
        api_response = api_result.json()
        # iterate over all price objects
        for price in api_response['data']:
            # try to save the price if it exists
            if price is not None:
                price = PriceForm({'ticker': price['symbol'],
                                   'exchange': price['exchange'],
                                   'date': price['date'],
                                   'price': round(price['close'], 2)
                                   })
                # returns false if there is already a price on this particular date
                if price.is_valid():
                    price.save()
            else:
                message = (
                    'We could not find one of the following symbols on Marketstack {}. '
                    'Take a look yourself: https://marketstack.com/search.'.format(symbols)
                )
                logger.info(message)
    except Exception as err:
        logger.error(err)
