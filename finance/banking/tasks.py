from finance.banking.models import Movie
from finance.banking.models import Depot

from background_task import background


@background
def update_movies_task(depot_pk):
    depot = Depot.objects.get(pk=depot_pk)

    accounts = depot.accounts.all()
    categories = depot.categories.all()

    for movie in Movie.objects.filter(depot=depot, account__in=accounts, category__in=categories):
        if movie.update_needed:
            movie.update()

    for movie in Movie.objects.filter(depot=depot, account__in=accounts, category=None):
        if movie.update_needed:
            movie.update()

    for movie in Movie.objects.filter(depot=depot, account=None, category__in=categories):
        if movie.update_needed:
            movie.update()

    for movie in Movie.objects.filter(depot=depot, account=None, category=None):
        if movie.update_needed:
            movie.update()
