from django.db.models.signals import post_save, post_delete
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils import timezone
from django.db import models

from finance.users.models import StandardUser
from finance.core.models import Timespan as CoreTimespan
from finance.core.models import Account as CoreAccount
from finance.core.models import Depot as CoreDepot

import pandas as pd
import numpy as np
import time


def init_alternative():
    pass


class Depot(CoreDepot):
    user = models.ForeignKey(StandardUser, editable=False, related_name="alternative_depots",
                             on_delete=models.CASCADE)

    # getters
    def get_movie(self):
        return self.movies.get(depot=self, account=None, asset=None)


class Account(CoreAccount):
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name="accounts")

    # getters
    def get_movie(self):
        return self.movies.get(depot=self.depot, asset=None)


class Alternative(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name="alternatives")

    def __str__(self):
        return "{}".format(self.name)

    # getters
    def get_movie(self, depot):
        return self.movies.get(depot=depot, account=None)

    def get_acc_movie(self, depot, account):
        return self.movies.get(depot=depot, account=account)


class Value(models.Model):
    alternative = models.ForeignKey(Alternative, related_name="values", on_delete=models.PROTECT)
    date = models.DateTimeField()
    value = models.DecimalField(decimal_places=2, max_digits=15, default=0)

    class Meta:
        unique_together = ("alternative", "date")

    def __str__(self):
        return "{} {} {}".format(self.alternative, self.get_date(), self.value)

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y")


class Flow(models.Model):
    alternative = models.ForeignKey(Alternative, related_name="flows", on_delete=models.PROTECT)
    date = models.DateTimeField()
    flow = models.DecimalField(decimal_places=2, max_digits=15, default=0)

    class Meta:
        unique_together = ("alternative", "date")

    def __str__(self):
        return "{} {} {}".format(self.alternative, self.get_date(), self.flow)

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y")


class Timespan(CoreTimespan):
    depot = models.ForeignKey(Depot, editable=False, related_name="timespans",
                              on_delete=models.CASCADE)

    # getters
    def get_start_date(self):
        return timezone.localtime(self.start_date).strftime("%d.%m.%Y %H:%M") if self.start_date else None

    def get_end_date(self):
        return timezone.localtime(self.end_date).strftime("%d.%m.%Y %H:%M") if self.end_date else None


class Movie(models.Model):
    update_needed = models.BooleanField(default=True)
    depot = models.ForeignKey(Depot, blank=True, null=True, related_name="movies",
                              on_delete=models.CASCADE)
    account = models.ForeignKey(Account, blank=True, null=True, related_name="movies",
                                on_delete=models.CASCADE)
    alternative = models.ForeignKey(Alternative, blank=True, null=True, related_name="movies", on_delete=models.CASCADE)


class Picture(models.Model):
    movie = models.ForeignKey(Movie, related_name="pictures", on_delete=models.CASCADE)
    d = models.DateTimeField()

    p = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)
    v = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)
    g = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)
    cr = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)
    ttwr = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)
    ca = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=8)
    cs = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)


# post_save.connect(Movie.init_update, sender=Price)
# post_delete.connect(Movie.init_update, sender=Price)
# post_save.connect(Movie.init_update, sender=Trade)
# post_delete.connect(Movie.init_update, sender=Trade)
# post_save.connect(Movie.init_update, sender=Transaction)
# post_delete.connect(Movie.init_update, sender=Transaction)
# post_save.connect(Movie.init_movies, sender=Account)
# post_save.connect(Movie.init_movies, sender=Asset)
# post_save.connect(Movie.init_movies, sender=Depot)
