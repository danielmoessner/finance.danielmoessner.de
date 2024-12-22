from django.contrib import admin

from apps.stocks.models import PriceFetcher

admin.site.register(PriceFetcher)
