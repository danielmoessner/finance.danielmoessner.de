from django.conf import settings
from django.db.utils import IntegrityError

from .models import Asset
from .models import Price
from .models import Depot
from .models import Movie

from background_task import background
from datetime import timedelta
from datetime import datetime
from datetime import time
from os.path import isfile, join
from os import listdir
import urllib.request
import urllib.error
import logging
import json
import pytz
import os


logger = logging.getLogger("background_tasks")


@background()
def update_movies_task(depot_pk):
    depot = Depot.objects.get(pk=depot_pk)

    for account in depot.accounts.all():
        for asset in depot.assets.exclude(symbol=depot.user.currency):
            movie, created = Movie.objects.get_or_create(depot=depot, account=account, asset=asset)
            if movie.update_needed:
                movie.update()
        movie, created = Movie.objects.get_or_create(depot=depot, account=account, asset=None)
        if movie.update_needed:
            movie.update()
    for asset in depot.assets.exclude(symbol=depot.user.currency):
        movie, created = Movie.objects.get_or_create(depot=depot, account=None, asset=asset)
        if movie.update_needed:
            movie.update()
    movie, created = Movie.objects.get_or_create(depot=depot, account=None, asset=None)
    if movie.update_needed:
        movie.update()


@background()
def update_prices():
    # fetch
    time_now = datetime.now()
    file_path = os.path.join(settings.MEDIA_ROOT, "crypto/prices")
    file_name = datetime.strftime(time_now, "%Y%m%d") + ".json"
    file = os.path.join(file_path, file_name)
    if not os.path.exists(file):
        text = "{} - Fetching coinmarketcap prices.".format(time_now)
        logger.info(text)
        try:
            with urllib.request.urlopen("https://api.coinmarketcap.com/v1/ticker/?convert=EUR") \
                    as url:
                data = json.loads(url.read().decode())
                file_path = os.path.join(settings.MEDIA_ROOT, "crypto/prices")
                file_name = datetime.strftime(time_now, "%Y%m%d") + ".json"
                file = os.path.join(file_path, file_name)
                with open(file, "w+") as file:
                    json.dump(data, file)
        except urllib.error.HTTPError as e:
            logger.error(str(e))
    else:
        text = "{} - Prices have already been fetched.".format(time_now)
        logger.info(text)
        return
    # update
    file_path = os.path.join(settings.MEDIA_ROOT, "crypto/prices")
    files = [f for f in listdir(file_path) if isfile(join(file_path, f))]
    for file in files:
        try:
            date = datetime.strptime(file[:-5], "%Y%m%d")
        except ValueError:
            break
        date_start = pytz.utc.localize(
            datetime.combine(date, time(hour=0, minute=0))) - timedelta(hours=6)
        date_end = pytz.utc.localize(
            datetime.combine(date, time(hour=23, minute=59, second=59))) + timedelta(hours=6)
        for asset in Asset.objects.filter(private_name=None, private_symbol=None).exclude(
                symbol="EUR"):
            if not Price.objects.filter(asset=asset, currency="EUR", date__gte=date_start,
                                        date__lte=date_end).exists():
                with open(os.path.join(file_path, file), "r") as f:
                    data = json.load(f)
                    for entry in data:
                        if entry["symbol"] == asset.symbol:
                            pprice = entry["price_" + "eur"]
                            pdate = pytz.utc.localize(
                                datetime.fromtimestamp(int(entry["last_updated"])))
                            try:
                                Price.objects.create(asset=asset, currency="EUR", date=pdate,
                                                     price=pprice)
                            except IntegrityError:
                                text = "{} - Integrity Error: {} --filedate: {} --assetdate: {}"\
                                    .format(time_now, asset, date, pdate)
                                logger.warning(text)
                            break
