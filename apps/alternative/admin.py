from django.contrib import admin

from .models import Depot
from .models import Alternative
from .models import Value
from .models import Flow
from .models import Movie
from .models import Picture

admin.site.register(Depot)
admin.site.register(Alternative)
admin.site.register(Value)
admin.site.register(Flow)
admin.site.register(Movie)
admin.site.register(Picture)
