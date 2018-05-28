from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db import models

from finance.core.models import IntelligentTimespan as CoreIntelligentTimespan
from finance.core.models import Account as CoreAccount
from finance.core.models import Depot as CoreDepot
from finance.users.models import StandardUser
from finance.core.utils import create_slug

import pandas as pd
import numpy as np
import time


class Timespan(CoreIntelligentTimespan):
    user = models.ForeignKey(StandardUser, editable=False, on_delete=models.CASCADE,
                             related_name="banking_timespans")

    @staticmethod
    def get_default_intelligent_timespan():
        ts, created = Timespan.objects.get_or_create(
            name="Default Timespan", start_date=None, end_date=None)
        return ts


class Depot(CoreDepot):
    user = models.ForeignKey(StandardUser, editable=False, related_name="banking_depots",
                             on_delete=models.CASCADE)
    timespan = models.ForeignKey(
        Timespan, related_name="depots",
        on_delete=models.PROTECT,
        null=True
    )

    def __init__(self, *args, **kwargs):
        super(Depot, self).__init__(*args, **kwargs)
        self.m = None

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super(Depot, self).save(force_insert, force_update, using, update_fields)
        Movie.update_all(depot=self, disable_update=True)

    # getters
    def get_movie(self):
        if not self.m:
            self.m = Movie.objects.get(depot=self, account=None, category=None)
        return self.m


class Account(CoreAccount):
    depot = models.ForeignKey(Depot, on_delete=models.PROTECT, related_name="accounts")

    def __init__(self, *args, **kwargs):
        super(Account, self).__init__(*args, **kwargs)
        self.m = None

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super(Account, self).save(force_insert, force_update, using, update_fields)
        Movie.update_all(depot=self.depot, disable_update=True)

    # getters
    def get_movie(self):
        if not self.m:
            self.m = Movie.objects.get(depot=self.depot, account=self, category=None)
        return self.m


class Category(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    depot = models.ForeignKey(Depot, editable=False, related_name="categories",
                              on_delete=models.CASCADE)

    def __init__(self, *args, **kwargs):
        super(Category, self).__init__(*args, **kwargs)
        self.s = None  # stats

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.slug:
            self.slug = create_slug(self)
        super(Category, self).save(force_insert, force_update, using, update_fields)
        Movie.update_all(depot=self.depot, disable_update=True)

    # getters
    def get_movie(self):
        if not self.s:
            depot = Depot.objects.filter(user=self.user, is_active=True)
            self.s = Movie.objects.get(depot=depot, category=self, account=None)
        return self.s

    @staticmethod
    def get_default_category():
        return Category.objects.get_or_create(
            name="Default Category",
            description="This category was created because the original category got deleted.")


class Change(models.Model):
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="changes")
    date = models.DateTimeField()
    category = models.ForeignKey(Category, related_name="changes", null=True,
                                 on_delete=models.SET(Category.get_default_category))
    description = models.TextField(blank=True)
    change = models.DecimalField(decimal_places=2, max_digits=15)

    def __str__(self):
        account = self.account.name
        date = self.date.strftime(self.account.depot.user.date_format)
        change = str(self.change)
        return account + " " + date + " " + change + " " + str(self.pk)

    def save(self, *args, **kwargs):
        date = self.date
        if self.pk:
            date = min(self.date, Picture.objects.filter(change=self).first().d)
        movies = Movie.objects.filter(
            Q(depot=self.account.depot, account=None, category=None) |
            Q(depot=self.account.depot, account=self.account, category=None) |
            Q(depot=self.account.depot, account=None, category=self.category) |
            Q(depot=self.account.depot, account=self.account, category=self.category)
        )
        [movie.pictures.filter(d__gte=date).delete() for movie in movies]
        for movie in movies:
            movie.update_needed = True
            movie.save()
        super(Change, self).save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        movies = Movie.objects.filter(
            Q(depot=self.account.depot, account=None, category=None) |
            Q(depot=self.account.depot, account=self.account, category=None) |
            Q(depot=self.account.depot, account=None, category=self.category) |
            Q(depot=self.account.depot, account=self.account, category=self.category)
        )
        [movie.pictures.filter(d__gte=self.date).delete() for movie in movies]
        for movie in movies:
            movie.update_needed = True
            movie.save()
        super(Change, self).delete(using, keep_parents)

    # getters
    def get_date(self, user):
        # user in args because of sql query optimization
        return self.date.strftime(user.date_format)

    def get_balance(self, movie):
        try:
            return self.pictures.get(movie=movie).b
        except Picture.DoesNotExist:
            return "update"

    def get_description(self):
        description = self.description[:35]
        if len(description) < len(self.description):
            description += "..."
        return description


class Movie(models.Model):
    update_needed = models.BooleanField(default=True)
    depot = models.ForeignKey(Depot, blank=True, null=True, on_delete=models.CASCADE,
                              related_name="movies")
    account = models.ForeignKey(Account, blank=True, null=True, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, blank=True, null=True, related_name="stats",
                                 on_delete=models.CASCADE)

    class Meta:
        unique_together = ("depot", "account", "category")

    def __init__(self, *args, **kwargs):
        super(Movie, self).__init__(*args, **kwargs)
        self.data = None
        self.timespan_data = None

    def __str__(self):
        text = "{} {} {}".format(self.depot, self.account, self.category)
        return text.replace("None", "").replace("   ", " ").replace("  ", " ")

    # getters
    def get_df(self, timespan=None):
        if timespan and timespan.start_date and timespan.end_date:
            pictures = self.pictures.filter(d__gte=timespan.start_date,
                                            d__lte=timespan.end_date).values("d", "c", "b")
        else:
            pictures = self.pictures.values("d", "c", "b")
        df = pd.DataFrame(list(pictures))
        return df

    def get_data(self, timespan=None):
        if timespan and timespan.start_date and timespan.end_date:
            pictures = self.pictures.filter(d__gte=timespan.start_date,
                                            d__lte=timespan.end_date).values("d", "c", "b")
        else:
            pictures = Picture.objects.filter(movie=self)
        data = dict()
        data["d"] = (pictures.values_list("d", flat=True))
        data["b"] = (pictures.values_list("b", flat=True))
        data["c"] = (pictures.values_list("c", flat=True))
        self.data = data
        return self.data

    def get_value(self, user, timespan, keys):
        # user in args for query optimization and ease
        data = dict()
        start_picture = None
        end_picture = None
        if timespan.start_date:
            data["start_date"] = timespan.start_date.strftime(user.date_format)
            try:
                start_picture = self.pictures.filter(d__lt=timespan.start_date).latest("d")
            except ObjectDoesNotExist:
                pass
        if timespan.end_date:
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
        return data

    def get_total(self):
        try:
            return self.pictures.latest("d").b
        except ObjectDoesNotExist:
            return 0

    # update
    @staticmethod
    def update_all(depot, disable_update=False, force_update=False):
        if force_update:
            Movie.objects.filter(depot=depot).delete()

        t1 = time.time()
        for account in depot.accounts.all():
            for category in Category.objects.all():
                movie, created = Movie.objects.get_or_create(depot=depot, account=account,
                                                             category=category)
                if not disable_update and movie.update_needed:
                    movie.update()
            movie, created = Movie.objects.get_or_create(depot=depot, account=account,
                                                         category=None)
            if not disable_update and movie.update_needed:
                movie.update()
        for category in depot.categories.all():
            movie, created = Movie.objects.get_or_create(depot=depot, account=None,
                                                         category=category)
            if not disable_update and movie.update_needed:
                movie.update()
        movie, created = Movie.objects.get_or_create(depot=depot, account=None,
                                                     category=None)
        if not disable_update and movie.update_needed:
            movie.update()
        t2 = time.time()

        print("this took", str((t2 - t1) / 60), "minutes")

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
        print(self, "is up to date.",
              "--Calc Time:", ((t3 - t2) / (t4-t2)),
              "--Save Time:", ((t4 - t3) / (t4-t2)))
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
