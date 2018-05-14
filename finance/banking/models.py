from django.db import models

from finance.core.models import IntelligentTimespan as CoreIntelligentTimespan
from finance.core.models import Timespan as CoreTimespan
from finance.core.models import Account as CoreAccount
from finance.core.models import Depot as CoreDepot
from finance.users.models import StandardUser
from finance.core.utils import create_slug

from datetime import datetime
import pytz
import time


class IntelligentTimespan(CoreIntelligentTimespan):
    user = models.ForeignKey(StandardUser, editable=False, on_delete=models.CASCADE,
                             related_name="banking_intelligent_timespans")

    # getters
    def get_timespans(self):
        timespans = self.timespans.order_by("end_date")
        return timespans

    @staticmethod
    def get_default_intelligent_timespan():
        pts, created = IntelligentTimespan.objects.get_or_create(
            name="Default Timespan", start_date=None, end_date=None)
        return pts

    # update
    @staticmethod
    def update_all():
        ts, created = IntelligentTimespan.objects.get_or_create(
            name="Default Timespan", start_date=None, period=None, end_date=None)

        for its in IntelligentTimespan.objects.all():
            its.create_timespans()

    def update(self):
        if self.start_date and self.period:
            Timespan.objects.get_or_create(
                self,
                self.start_date,
                self.start_date + self.period
            )
            while self.timespans.order_by("end_date").last().end_date <= datetime.now(tz=pytz.utc):
                Timespan.objects.get_or_create(
                    self,
                    self.timespans.order_by("end_date").last().end_date,
                    self.timespans.order_by("end_date").last().end_date + self.period
                )
        elif self.end_date and self.start_date:
            Timespan.objects.get_or_create(self, self.start_date, self.end_date)
        elif self.start_date:
            Timespan.objects.get_or_create(self, self.start_date, datetime.now(tz=pytz.utc))
        else:
            Timespan.objects.get_or_create(self, None, None)


class Timespan(CoreTimespan):
    timespan = models.ForeignKey(IntelligentTimespan, related_name="timespans",
                                 on_delete=models.CASCADE)


class Depot(CoreDepot):
    user = models.ForeignKey(StandardUser, editable=False, related_name="banking_depots",
                             on_delete=models.CASCADE)
    timespan = models.ForeignKey(
        IntelligentTimespan, related_name="depots",
        on_delete=models.SET(IntelligentTimespan.get_default_intelligent_timespan),
        null=True
    )

    def __init__(self, *args, **kwargs):
        super(Depot, self).__init__(*args, **kwargs)
        self.m = None

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
        Movie.update_all(disable_update=True)

    # getters
    def get_movie(self):
        if not self.m:
            self.m = Movie.objects.get(depot=self.depot, account=self, category=None)
        return self.m


class Category(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    user = models.ForeignKey(StandardUser, editable=False, related_name="categories")

    def __init__(self, *args, **kwargs):
        super(Category, self).__init__(*args, **kwargs)
        self.s = None  # stats

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.slug:
            self.slug = create_slug(self)
        super(Category, self).save(force_insert, force_update, using, update_fields)

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
        date = self.date.strftime(self.account.depot.date_format)
        description = str(self.description)
        return account + " " + date + " " + description

    def save(self, *args, **kwargs):
        movie = Movie.objects.get(depot=self.account.depot, account=None, category=None)
        [picture.delete() for picture in movie.pictures.filter(d__gte=self.date)]
        movie = Movie.objects.get(depot=self.account.depot, account=self.account, category=None)
        [picture.delete() for picture in movie.pictures.filter(d__gte=self.date)]
        movie = Movie.objects.get(depot=self.account.depot, account=self.account,
                                  category=self.category)
        [picture.delete() for picture in movie.pictures.filter(d__gte=self.date)]
        movie = Movie.objects.get(depot=self.account.depot, account=None, category=self.category)
        [picture.delete() for picture in movie.pictures.filter(d__gte=self.date)]
        if self.pk:
            [picture.delete() for picture in Picture.objects.filter(change=self).all()]
        super(Change, self).save(*args, **kwargs)

    def get_date(self):
        return self.date.strftime(self.account.depot.user.date_format)

    def get_balance(self, depot=None, account=None, category=None):
        movie = Movie.objects.filter(depot=depot, account=account, category=category)
        picture = Picture.objects.filter(change=self, movie=movie)
        if picture.exists():
            return picture.get().b
        else:
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
        return text.replace("None ", "").replace(" None", " ")

    # calc
    def get_c(self):
        """
        c(changes) = the changes
        """
        if self.depot and not self.account and not self.category:
            changes = Change.objects.filter(account__in=self.depot.accounts.all())
        elif self.account:
            changes = Change.objects.filter(account__in=self.depot.accounts.all()).filter(
                account=self.account)
        elif self.category:
            changes = Change.objects.filter(account__in=self.depot.accounts.all()).filter(
                category=self.category)
        else:
            raise Exception("Why is no account or category defined")
        changes = changes.order_by("date", "pk")
        if self.account and self.category:
            new_changes = list()
            for change in changes:
                if change.category != self.category:
                    change.change = 0
                new_changes.append(change)
            changes = new_changes
        # throw away the changes that already have a picture
        change_information_objects = Picture.objects.filter(movie=self).all()
        changes_len = len(changes)
        changes = changes[len(change_information_objects):]
        assert len(changes) == (changes_len - len(change_information_objects))
        return changes

    def calc_d(self):
        """
        d(dates) = the dates on which a change happened
        """
        d = list()
        for change in self.get_c():
            d.append(change.date)
        return d

    def calc_c(self):
        """
        c(change) = the change that occured on that date
        """
        c = list()
        for change in self.get_c():
            c.append(change.change)
        return c

    def calc_b(self):
        """
        b(balance) = the amount of money at the time
        """
        b = list()
        changes = self.get_c()
        if len(changes) == 0:
            return b
        changes = iter(changes)
        prev_b = self.get_data()["b"].last() if self.get_data()["b"].last() is not None else 0
        b.append((next(changes).change + prev_b))
        for change in changes:
            b.append(b[-1] + change.change)
        return b

    # update
    def update(self):
        def status(movie):
            movie.update_needed = False
            movie.save()
            done = len(Movie.objects.filter(update_needed=False))
            all = len(Movie.objects.filter().all())
            print(movie, "is up to date.")
        # data
        changes = self.get_c()
        d = self.calc_d()
        b = self.calc_b()
        c = self.calc_c()
        # assert
        assert len(d) == len(b) == len(c) == len(changes)
        # chain
        if len(Picture.objects.filter(movie=self).all()) > 0:
            prev_picture = Picture.objects.filter(movie=self).latest("d")
        else:
            prev_picture = None
        # save
        for i in range(len(d)):
            picture = Picture(movie=self, d=d[i], b=b[i], c=c[i], prev=prev_picture,
                              change=changes[i])
            picture.save()
            prev_picture = picture
        # status
        status(self)

    @staticmethod
    def update_all(disable_update=False):
        # update
        t1 = time.time()
        for depot in Depot.objects.all():
            for account in Account.objects.all():
                for category in Category.objects.all():
                    movie, created = Movie.objects.get_or_create(depot=depot, account=account,
                                                                 category=category)
                    if not disable_update:
                        movie.update()
                movie, created = Movie.objects.get_or_create(depot=depot, account=account,
                                                             category=None)
                if not disable_update:
                    movie.update()
            for category in Category.objects.all():
                movie, created = Movie.objects.get_or_create(depot=depot, account=None,
                                                             category=category)
                if not disable_update:
                    movie.update()
            movie, created = Movie.objects.get_or_create(depot=depot, account=None,
                                                         category=None)
            if not disable_update:
                movie.update()
        t2 = time.time()
        print("this took", str((t2 - t1) / 60), "minutes")

    # get
    def get_data(self):
        # if not self.data:
        data = dict()
        data["d"] = (Picture.objects.filter(movie=self).values_list("d", flat=True))
        data["b"] = (Picture.objects.filter(movie=self).values_list("b", flat=True))
        data["c"] = (Picture.objects.filter(movie=self).values_list("c", flat=True))
        self.data = data
        return self.data

    def get_timespan_data(self, parent_timespan):
        if not self.timespan_data:
            timespan = parent_timespan.get_timespans().last()
            data = dict()
            if timespan.start_date and timespan.end_date:
                data["d"] = (Picture.objects.filter(movie=self, d__gte=timespan.start_date,
                                                    d__lte=timespan.end_date)
                             .values_list("d", flat=True))
                data["b"] = (Picture.objects.filter(movie=self, d__gte=timespan.start_date,
                                                    d__lte=timespan.end_date)
                             .values_list("b", flat=True))
                data["c"] = (Picture.objects.filter(movie=self, d__gte=timespan.start_date,
                                                    d__lte=timespan.end_date)
                             .values_list("c", flat=True))
                self.timespan_data = data
            else:
                self.timespan_data = self.get_data()
        return self.timespan_data

    # template
    def get_total(self):
        return round(self.get_data()["b"].last(), 2) if self.get_data()["b"].last() is not None \
            else 0


class Picture(models.Model):
    movie = models.ForeignKey(Movie, related_name="pictures", on_delete=models.CASCADE)
    d = models.DateTimeField()
    b = models.DecimalField(max_digits=15, decimal_places=2)
    c = models.DecimalField(max_digits=15, decimal_places=2)
    change = models.ForeignKey(Change, on_delete=models.CASCADE, blank=True, null=True)
    prev = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True)

    # other
    def __str__(self):
        stats = str(self.movie)
        d = str(self.d)
        c = str(self.c)
        b = str(self.b)
        return stats + " " + d + " " + c + " " + b
