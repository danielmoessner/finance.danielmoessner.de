from django.utils import timezone

from .models import Asset, CoinGeckoAsset, Price

from background_task import background
from urllib.request import urlopen
import json


def create_coingecko_asset(symbol):
    url = 'https://api.coingecko.com/api/v3/coins/list'
    with urlopen(url) as response:
        all_available_coins = json.loads(response.read().decode())
        coins_i_am_looking_for = list(filter(lambda coin: coin['symbol'] == symbol.lower(), all_available_coins))
        if len(coins_i_am_looking_for) != 1:
            return None
        coin = coins_i_am_looking_for[0]
        CoinGeckoAsset.objects.create(coingecko_id=coin['id'], coingecko_symbol=coin['symbol'], symbol=symbol)


def fetch_price(coingecko_asset):
    url = 'https://api.coingecko.com/api/v3/simple/price?ids={}&vs_currencies=eur'.format(coingecko_asset.coingecko_id)
    with urlopen(url) as response:
        price = json.loads(response.read().decode())
        price = price[coingecko_asset.coingecko_id]['eur']
        Price.objects.create(symbol=coingecko_asset.symbol, price=price, date=timezone.now())


@background()
def update_prices():
    asset_symbols = Asset.objects.all().values_list('symbol', flat=True).distinct()
    # create coingecko connections for every asset that there is
    for symbol in asset_symbols:
        try:
            asset = CoinGeckoAsset.objects.get(symbol=symbol)
        except CoinGeckoAsset.DoesNotExist:
            create_coingecko_asset(symbol)
            # skip the price fetching for this asset at the moment
            continue
        fetch_price(asset)
