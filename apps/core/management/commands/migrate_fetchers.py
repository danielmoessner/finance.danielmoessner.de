from django.core.management.base import BaseCommand
from apps.crypto.models import Asset, CoinGeckoAsset

from apps.crypto.models import PriceFetcher


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for coingeckoasset in list(CoinGeckoAsset.objects.all()):
            assets = list(Asset.objects.filter(symbol=coingeckoasset.symbol))
            for asset in assets:
                if not PriceFetcher.objects.filter(asset__symbol=coingeckoasset.symbol).exists():
                    PriceFetcher.objects.create(
                        fetcher_type="COINGECKO",
                        asset=asset,
                        data={
                            "coingecko_id": coingeckoasset.coingecko_id,
                        },
                    )
