from background_task import background
from django.conf import settings
from .models import Stock
from .forms import PriceForm
import requests


# @background()
def fetch_prices():
    # create a list of all symbols for the query
    symbols = [stock.get_marketstack_symbol() for stock in list(Stock.objects.all())]
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
                                   'price': price['close']
                                   })
                # returns false if there is already a price on this particular date
                if price.is_valid():
                    price.save()
            else:
                print(
                    'We could not find one of the following symbols on Marketstack {}. '
                    'Take a look yourself: https://marketstack.com/search.'.format(symbols)
                )
    except Exception as err:
        print(err)
