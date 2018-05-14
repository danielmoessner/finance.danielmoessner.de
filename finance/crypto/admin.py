from django.contrib import admin

from .models import Depot
from .models import Asset
from .models import Price
from .models import Account
from .models import Trade
from .models import Movie
from .models import Picture

admin.site.register(Depot)
admin.site.register(Account)
admin.site.register(Trade)
admin.site.register(Asset)
admin.site.register(Price)
admin.site.register(Movie)
admin.site.register(Picture)
