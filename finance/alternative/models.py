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

    class Meta:
        unique_together = ("depot", "account", "alternative")

    def __str__(self):
        text = "{} {} {}".format(self.depot, self.account, self.alternative)
        return text.replace("None ", "").replace(" None", "")

    # getters
    def get_df(self, timespan=None):
        if timespan and timespan.start_date and timespan.end_date:
            pictures = self.pictures.filter(d__gte=timespan.start_date,
                                            d__lte=timespan.end_date)
        else:
            pictures = self.pictures
        pictures = pictures.order_by("d")
        pictures = pictures.values("d", "p", "v", "g", "cr", "ttwr", "ca", "cs")
        df = pd.DataFrame(list(pictures), dtype=np.float64)
        if df.empty:
            df = pd.DataFrame(columns=["d", "p", "v", "g", "cr", "ttwr", "ca", "cs"])
        return df

    def get_data(self, timespan=None):
        if timespan and timespan.start_date and timespan.end_date:
            pictures = self.pictures.filter(d__gte=timespan.start_date,
                                            d__lte=timespan.end_date)
        else:
            pictures = Picture.objects.filter(movie=self)
        pictures = pictures.order_by("d")
        data = dict()
        data["d"] = (pictures.values_list("d", flat=True))
        data["p"] = (pictures.values_list("p", flat=True))
        data["v"] = (pictures.values_list("v", flat=True))
        data["g"] = (pictures.values_list("g", flat=True))
        data["cr"] = (pictures.values_list("cr", flat=True))
        data["ttwr"] = (pictures.values_list("ttwr", flat=True))
        data["ca"] = (pictures.values_list("ca", flat=True))
        data["cs"] = (pictures.values_list("cs", flat=True))
        return data

    def get_values(self, user, keys, timespan=None):
        # user in args for query optimization and ease
        data = dict()
        start_picture = None
        end_picture = None
        if timespan and timespan.start_date:
            data["start_date"] = timespan.start_date.strftime(user.date_format)
            try:
                start_picture = self.pictures.filter(d__lt=timespan.start_date).latest("d")
            except ObjectDoesNotExist:
                pass
        if timespan and timespan.end_date:
            data["end_date"] = timespan.end_date.strftime(user.date_format)
            try:
                end_picture = self.pictures.filter(d__lte=timespan.end_date).latest("d")
            except ObjectDoesNotExist:
                pass
        else:
            try:
                end_picture = self.pictures.latest("d")
            except ObjectDoesNotExist:
                pass

        for key in keys:
            if start_picture and end_picture:
                data[key] = getattr(end_picture, key) - getattr(start_picture, key)
            elif end_picture:
                data[key] = getattr(end_picture, key)
            else:
                data[key] = 0
            if user.rounded_numbers:
                data[key] = round(data[key], 2)
                if data[key] == 0.00:
                    data[key] = "x"

        return data

    # init
    @staticmethod
    def init_movies(sender, instance, **kwargs):
        if sender is Account:
            depot = instance.depot
            for alternative in depot.alternatives.all():
                Movie.objects.get_or_create(depot=depot, account=instance, alternative=alternative)
            Movie.objects.get_or_create(depot=depot, account=instance, alternative=None)
        elif sender is Alternative:
            depot = instance.depot
            for account in depot.accounts.all():
                Movie.objects.get_or_create(depot=depot, account=account, alternative=instance)
            Movie.objects.get_or_create(depot=depot, account=instance, alternative=None)
        elif sender is Depot:
            depot = instance
            Movie.objects.get_or_create(depot=depot, account=None, alternative=None)

    @staticmethod
    def init_update(sender, instance, **kwargs):
        if sender is Value:
            q1 = Q(alternative=instance.alternative)
            q2 = Q(depot=instance.alternative.depot, alternative=None, account=None)
            movies = Movie.objects.filter(q1 | q2)
            movies.update(update_needed=True)
        elif sender is Flow:
            q1 = Q(alternative=instance.alternative)
            q2 = Q(depot=instance.alternative.depot, alternative=None, account=None)
            movies = Movie.objects.filter(q1 | q2)
            movies.update(update_needed=True)


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


post_save.connect(Movie.init_update, sender=Value)
post_delete.connect(Movie.init_update, sender=Value)
post_save.connect(Movie.init_update, sender=Flow)
post_delete.connect(Movie.init_update, sender=Flow)
post_save.connect(Movie.init_movies, sender=Account)
post_save.connect(Movie.init_movies, sender=Alternative)
post_save.connect(Movie.init_movies, sender=Depot)
