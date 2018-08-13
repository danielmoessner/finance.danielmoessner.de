from django.contrib import admin

# Register your models here.
from .models import Account
from .models import Change
from .models import Category
from .models import Depot
from .models import Picture
from .models import Movie
from .models import Timespan

admin.site.register(Timespan)
admin.site.register(Movie)
admin.site.register(Picture)
admin.site.register(Account)
admin.site.register(Category)
admin.site.register(Change)
admin.site.register(Depot)
