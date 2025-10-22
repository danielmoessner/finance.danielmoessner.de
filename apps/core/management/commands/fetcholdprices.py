import json
import warnings
from datetime import datetime

import requests
from django.core.management.base import BaseCommand

from apps.crypto.models import Asset, Price

warnings.simplefilter("error", FutureWarning)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        mapping = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "ADA": "cardano",
        }
        for asset in Asset.objects.filter(symbol__in=["BTC", "ETH", "ADA"]):
            id = mapping[asset.symbol]
            url = f"https://api.coingecko.com/api/v3/coins/{id}/market_chart?vs_currency=eur&days=30"
            response = requests.get(url)
            prices = json.loads(response.content.decode())["prices"]
            for t, p in prices:
                date = datetime.fromtimestamp(t / 1000)
                if not Price.objects.filter(
                    symbol=asset.symbol, date__date=date.date()
                ).exists():
                    price = Price.objects.create(
                        symbol=asset.symbol, date=date, price=p
                    )
                    self.stdout.write(
                        f"Saved {asset.symbol} price {price.price} for {date}"
                    )
