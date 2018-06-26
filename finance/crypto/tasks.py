from background_task import background
from django.conf import settings
import logging

import urllib.request
import urllib.error
import json
import time
import os


logger = logging.getLogger("background_tasks")


@background()
def update_prices():
    file_path = os.path.join(settings.MEDIA_ROOT, "crypto/prices")
    file_name = time.strftime("%Y%m%d") + ".json"
    file = os.path.join(file_path, file_name)
    if not os.path.exists(file):
        try:
            with urllib.request.urlopen("https://api.coinmarketcap.com/v1/ticker/?convert=EUR") \
                    as url:
                data = json.loads(url.read().decode())
                file_path = os.path.join(settings.MEDIA_ROOT, "crypto/prices")
                file_name = time.strftime("%Y%m%d") + ".json"
                file = os.path.join(file_path, file_name)
                with open(file, "w+") as file:
                    json.dump(data, file)
            logger.debug("Price data was successfully pulled.")
        except urllib.error.HTTPError as e:
            logger.error(str(e))
