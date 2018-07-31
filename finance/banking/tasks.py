from finance.banking.models import Category
from finance.banking.models import Movie
from finance.banking.models import Depot

from background_task import background


@background
def update_movies_task(depot_pk, disable_update=False, force_update=False):
    depot = Depot.objects.get(pk=depot_pk)

    if force_update:
        depot.movies.all().delete()

    for account in depot.accounts.all():
        for category in Category.objects.all():
            movie, created = Movie.objects.get_or_create(depot=depot, account=account,
                                                         category=category)
            if not disable_update and movie.update_needed:
                movie.update()
        movie, created = Movie.objects.get_or_create(depot=depot, account=account, category=None)
        if not disable_update and movie.update_needed:
            movie.update()
    for category in depot.categories.all():
        movie, created = Movie.objects.get_or_create(depot=depot, account=None, category=category)
        if not disable_update and movie.update_needed:
            movie.update()
    movie, created = Movie.objects.get_or_create(depot=depot, account=None, category=None)
    if not disable_update and movie.update_needed:
        movie.update()
