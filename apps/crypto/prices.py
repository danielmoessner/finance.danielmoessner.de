from .models import Asset
from .models import Price
import pytz
import urllib
import json
import time
from datetime import datetime
from django import db


assets = Asset.objects.exclude(symbol="EUR")

names = list()
for asset in assets:
    names.append(str(asset.name).lower())
names = [name.replace("bitcoin cash", "bitcoin-cash") for name in names]
names = [name.replace("golem", "golem-network-tokens") for name in names]
names = [name.replace("bitcoin gold", "bitcoin-gold") for name in names]

urls = list()
for name in names:
    urls.append("https://coinmarketcap.northpole.ro/history.json?period=2017&coin=" + name)


def fetch():
    for i in range(len(urls)):
        try:
            with urllib.request.urlopen(urls[i]) as url:
                data = json.loads(url.read().decode())
                for entry in data["history"]:
                    data_price = entry["price"]["eur"]
                    data_time = int(entry["timestamp"])
                    data_time = datetime.fromtimestamp(data_time)
                    data_time = data_time.replace(tzinfo=pytz.utc)
                    if datetime(2017, 11, 1, 0, 0, tzinfo=pytz.UTC) < data_time:
                        data_asset = assets[i]
                        price = Price(asset=data_asset, date=data_time, price=data_price, currency="EUR")
                        # print(price)
                        try:
                            price.save()
                        except db.utils.IntegrityError:
                            pass
        except urllib.error.HTTPError:
            print("error with url", urls[i])
            continue
        print("saved prices of", urls[i])
        time.sleep(1)


fetch()
