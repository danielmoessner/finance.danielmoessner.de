from datetime import timedelta
from django.utils import timezone

from .models import Asset, CoinGeckoAsset, Price

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


def fetch_price(coingecko_assets: list[CoinGeckoAsset]):
    ids = ','.join([asset.coingecko_id for asset in coingecko_assets])
    url = 'https://api.coingecko.com/api/v3/simple/price?ids={}&vs_currencies=eur'.format(ids)
    with urlopen(url) as response:
        prices = json.loads(response.read().decode())
    for asset in coingecko_assets:
        price = prices[asset.coingecko_id]['eur']
        Price.objects.create(symbol=asset.symbol, price=price, date=timezone.now())


def update_prices():
    asset_symbols = Asset.objects.all().values_list('symbol', flat=True).distinct()
    coingecko_assets = []
    # create coingecko connections for every asset that there is
    for symbol in asset_symbols:
        try:
            asset = CoinGeckoAsset.objects.get(symbol=symbol)
            if Price.objects.filter(symbol=asset.symbol, date__gt=timezone.now() - timedelta(days=1)).exists():
                continue
            coingecko_assets.append(asset)
        except CoinGeckoAsset.DoesNotExist:
            create_coingecko_asset(symbol)
            # skip the price fetching for this asset at the moment
            continue
    fetch_price(coingecko_assets)
