import importlib
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.stocks.models import PriceFetcher, Stock


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for fetcher in list(PriceFetcher.objects.all()):
            if fetcher.type == "WEBSITE":
                fetcher.data = {
                    "website": fetcher.website,
                    "target": fetcher.target,
                }
                fetcher.save()

        for stock in list(Stock.objects.all()):
            if not stock.price_fetchers.exists():
                PriceFetcher.objects.create(
                    type="MARKETSTACK",
                    stock=stock,
                    data={
                        "symbol": stock.get_marketstack_symbol(),
                    },
                )

