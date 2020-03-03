from django.db.models.signals import pre_delete, pre_save, post_save
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db import models

from finance.users.models import StandardUser
from finance.core.models import Timespan as CoreTimespan
from finance.core.models import Account as CoreAccount
from finance.core.models import Depot as CoreDepot

import pandas as pd
import numpy as np
import time


class Depot(CoreDepot):
    user = models.ForeignKey(StandardUser, editable=False, related_name="banking_depots",
                             on_delete=models.CASCADE)

    # getters
    @staticmethod
    def get_objects_by_user(user):
        return Depot.objects.filter(user=user)

    def get_movie(self):
        return self.movies.get(account=None, category=None)

    # movies
    def reset_movies(self, delete=False):
        if delete:
            self.movies.all().delete()

        for account in self.accounts.all():
            for category in self.categories.all():
                Movie.objects.get_or_create(depot=self, account=account, category=category)
            Movie.objects.get_or_create(depot=self, account=account, category=None)
        for category in self.categories.all():
            Movie.objects.get_or_create(depot=self, account=None, category=category)
        Movie.objects.get_or_create(depot=self, account=None, category=None)

    def update_movies(self, force_update=False):
        if force_update:
            self.movies.update(update_needed=True)

        accounts = self.accounts.all()
        categories = self.categories.all()
        for movie in Movie.objects.filter(depot=self, account__in=accounts, category__in=categories):
            if movie.update_needed:
                movie.update()
        for movie in Movie.objects.filter(depot=self, account__in=accounts, category=None):
            if movie.update_needed:
                movie.update()
        for movie in Movie.objects.filter(depot=self, account=None, category__in=categories):
            if movie.update_needed:
                movie.update()
        for movie in Movie.objects.filter(depot=self, account=None, category=None):
            if movie.update_needed:
                movie.update()


class Account(CoreAccount):
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name="accounts")

    # getters
    @staticmethod
    def get_objects_by_user(user):
        return Account.objects.filter(depot__in=Depot.objects.filter(user=user))

    @staticmethod
    def get_objects_by_depot(depot):
        return Account.objects.filter(depot=depot)

    def get_movie(self):
        return self.movies.get(depot=self.depot, category=None)

    def get_cat_movie(self, category):
        return self.movies.get(depot=self.depot, category=category)


class Category(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    depot = models.ForeignKey(Depot, editable=False, related_name="categories",
                              on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    # getters
    @staticmethod
    def get_objects_by_user(user):
        return Category.objects.filter(depot__in=Depot.objects.filter(user=user))

    @staticmethod
    def get_objects_by_depot(depot):
        return Category.objects.filter(depot=depot)

    def get_movie(self):
        return self.movies.get(depot=self.depot, account=None)

    @staticmethod
    def get_default_category():
        return Category.objects.get_or_create(
            name="Default Category",
            description="This category was created because the original category got deleted.")


class Change(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="changes")
    date = models.DateTimeField()
    category = models.ForeignKey(Category, related_name="changes", null=True,
                                 on_delete=models.SET_NULL)
    description = models.TextField(blank=True)
    change = models.DecimalField(decimal_places=2, max_digits=15)

    def __str__(self):
        account = self.account.name
        date = self.date.strftime(self.account.depot.user.date_format)
        change = str(self.change)
        return account + " " + date + " " + change + " " + str(self.pk)

    # getters
    @staticmethod
    def get_objects(user):
        return Change.objects.filter(account__in=Account.get_objects_by_user(user))

    def get_date(self, user):
        # user in args because of sql query optimization
        return self.date.strftime(user.date_format)

    def get_balance(self, movie):
        try:
            return self.pictures.get(movie=movie).b
        except Picture.DoesNotExist:
            return "update"

    def get_description(self):
        description = self.description
        if len(str(self.description)) > 35:
            description = self.description[:35] + "..."
        return description


class Timespan(CoreTimespan):
    depot = models.ForeignKey(Depot, editable=False, related_name="timespans",
                              on_delete=models.CASCADE)


class Movie(models.Model):
    update_needed = models.BooleanField(default=True)
    depot = models.ForeignKey(Depot, blank=True, null=True, on_delete=models.CASCADE, related_name="movies")
    account = models.ForeignKey(Account, blank=True, null=True, on_delete=models.CASCADE, related_name="movies")
    category = models.ForeignKey(Category, blank=True, null=True, related_name="movies", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("depot", "account", "category")

    def __init__(self, *args, **kwargs):
        super(Movie, self).__init__(*args, **kwargs)
        self.data = None
        self.timespan_data = None

    def __str__(self):
        text = "{} {} {}".format(self.depot, self.account, self.category)
        return text.replace("None ", "").replace(" None", "")

    # getters
    def get_df(self, timespan=None):
        if timespan and timespan.start_date and timespan.end_date:
            pictures = self.pictures.filter(d__gte=timespan.start_date,
                                            d__lte=timespan.end_date).values("d", "c", "b")
        else:
            pictures = self.pictures.values("d", "c", "b")
        pictures = pictures.order_by("d")
        df = pd.DataFrame(list(pictures))
        if df.empty:
            df = pd.DataFrame(columns=["d", "c", "b"])
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
        data["b"] = (pictures.values_list("b", flat=True))
        data["c"] = (pictures.values_list("c", flat=True))
        return data

    def get_values(self, user, keys, timespan=None):
        # user in args for query optimization and ease
        data = dict()
        start_picture = None
        end_picture = None
        if timespan and timespan.start_date:
            data["start_date"] = timespan.start_date.strftime(user.date_format)
            try:
                start_picture = self.pictures.filter(d__lt=timespan.start_date).order_by(
                    "d", "pk").last()
            except ObjectDoesNotExist:
                pass
        if timespan and timespan.end_date:
            data["end_date"] = timespan.end_date.strftime(user.date_format)
            try:
                end_picture = self.pictures.filter(d__lte=timespan.end_date).order_by(
                    "d", "pk").last()
            except ObjectDoesNotExist:
                pass
        else:
            try:
                end_picture = self.pictures.order_by("d", "pk").last()
            except ObjectDoesNotExist:
                pass

        for key in keys:
            if start_picture and end_picture:
                data[key] = getattr(end_picture, key) - getattr(start_picture, key)
            elif end_picture:
                data[key] = getattr(end_picture, key)
            else:
                data[key] = "x"

            if data[key] == "x" or data[key] is None:
                pass
            else:
                data[key] = "{} {}".format(round(data[key], 2), user.get_currency_display())

        return data

    # update
    @staticmethod
    def init_movies(sender, instance, **kwargs):
        if sender is Account:
            depot = instance.depot
            for category in depot.categories.all():
                Movie.objects.get_or_create(depot=depot, account=instance, category=category)
            Movie.objects.get_or_create(depot=depot, account=instance, category=None)
        elif sender is Category:
            depot = instance.depot
            Movie.objects.get_or_create(depot=depot, account=None, category=instance)
        elif sender is Depot:
            depot = instance
            Movie.objects.get_or_create(depot=depot, account=None, category=None)

    @staticmethod
    def init_update(sender, instance, **kwargs):
        if sender is Change:
            depot = instance.account.depot
            q1 = Q(depot=depot, account=None, category=None)
            q2 = Q(depot=depot, account=instance.account, category=None)
            q3 = Q(depot=depot, account=None, category=instance.category)
            q4 = Q(depot=depot, account=instance.account, category=instance.category)
            movies = Movie.objects.filter(q1 | q2 | q3 | q4)
            date = instance.date
            pictures = Picture.objects.filter(change=instance)
            if instance.pk and pictures.exists():
                date = min(instance.date, pictures.first().d)
            Picture.objects.filter(movie__in=movies, d__gte=date).delete()
            movies.update(update_needed=True)

    def update(self):
        t2 = time.time()
        df = self.calc()

        t3 = time.time()
        pictures = list()
        for index, row in df.iterrows():
            picture = Picture(
                movie=self,
                d=index,
                c=row["c"],
                b=row["b"],
                change=Change.objects.get(pk=row["change_id"]),
            )
            pictures.append(picture)
        Picture.objects.bulk_create(pictures)

        t4 = time.time()
        text = "{} is up to date. --Calc Time: {}% --Save Time: {}%".format(
            self, round((t3 - t2) / (t4 - t2), 2), round((t4 - t3) / (t4 - t2), 2), "%")
        print(text)
        self.update_needed = False
        self.save()

    # calc helpers
    @staticmethod
    def fadd(df, column):
        """
        fadd: Sums up the column from the back to the front.
        """
        for i in range(1, len(df[column])):
            df.loc[df.index[i], column] = df[column][i - 1] + df[column][i]

    # calc
    def calc(self):
        df = pd.DataFrame()

        try:
            latest_picture = self.pictures.order_by("-d", "-pk")[0]  # change to latest django 1.20
            q = Q(date__gte=latest_picture.d)
        except IndexError:  # Picture.DoesNotExist: change back to that on django 1.20
            latest_picture = None
            q = Q()

        if self.account and self.category:
            changes = Change.objects.filter(
                Q(account=self.account, category=self.category) & q
            ).exclude(pk__in=self.pictures.values_list("change", flat=True)).order_by("date", "pk")
        elif self.account:
            changes = Change.objects.filter(
                Q(account=self.account) & q
            ).exclude(pk__in=self.pictures.values_list("change", flat=True)).order_by("date", "pk")
        elif self.category:
            changes = Change.objects.filter(
                Q(category=self.category) & q
            ).exclude(pk__in=self.pictures.values_list("change", flat=True)).order_by("date", "pk")
        elif self.depot:
            changes = Change.objects.filter(
                Q(account__in=self.depot.accounts.all()) & q
            ).exclude(pk__in=self.pictures.values_list("change", flat=True)).order_by("date", "pk")
        else:
            raise Exception("Why is no depot, account or category defined?")

        df["d"] = [change.date for change in changes]
        df["c"] = [change.change for change in changes]
        df["b"] = [change.change for change in changes]
        Movie.fadd(df, "b")
        if latest_picture:
            df["b"] += latest_picture.b
        df["change_id"] = [change.pk for change in changes]
        df.set_index("d", inplace=True)
        for column in df.drop(["change_id"], 1):
            df[column] = df[column].astype(np.float64)

        return df


class Picture(models.Model):
    movie = models.ForeignKey(Movie, related_name="pictures", on_delete=models.CASCADE)
    d = models.DateTimeField()
    b = models.DecimalField(max_digits=15, decimal_places=2)
    c = models.DecimalField(max_digits=15, decimal_places=2)
    change = models.ForeignKey(Change, on_delete=models.CASCADE, blank=True, null=True,
                               related_name="pictures")
    prev = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        stats = str(self.movie)
        d = str(self.d)
        c = str(self.c)
        b = str(self.b)
        return stats + " " + d + " " + c + " " + b


pre_save.connect(Movie.init_update, sender=Change)
pre_delete.connect(Movie.init_update, sender=Change)
post_save.connect(Movie.init_movies, sender=Account)
post_save.connect(Movie.init_movies, sender=Category)
post_save.connect(Movie.init_movies, sender=Depot)
