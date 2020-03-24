from django.contrib import admin

from .models import Account
from .models import Change
from .models import Category
from .models import Depot


admin.site.register(Account)
admin.site.register(Category)
admin.site.register(Change)
admin.site.register(Depot)
