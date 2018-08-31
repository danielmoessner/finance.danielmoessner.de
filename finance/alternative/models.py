from django.db.models.signals import post_save, post_delete
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator
from django.db.models import Q
from django.utils import timezone
from django.db import models

from finance.users.models import StandardUser
from finance.core.models import Timespan as CoreTimespan
from finance.core.models import Depot as CoreDepot
from finance.core.utils import print_df

from decimal import Decimal
import pandas as pd
import numpy as np
import time


def init_alternative(user):
    pass


class Depot(CoreDepot):
    user = models.ForeignKey(StandardUser, editable=False, related_name="alternative_depots",
                             on_delete=models.CASCADE)

    # getters
    def get_movie(self):
        return self.movies.get(depot=self, alternative=None)

    # movies
    def reset_movies(self, delete=False):
        if delete:
            self.movies.all().delete()

        for alternative in self.alternatives.all():
            Movie.objects.get_or_create(depot=self, alternative=alternative)
        Movie.objects.get_or_create(depot=self, alternative=None)

    def update_movies(self, force_update=False):
        if force_update:
            self.movies.update(update_needed=True)

        for movie in Movie.objects.filter(depot=self, alternative__in=self.alternatives.all()):
            if movie.update_needed:
                movie.update()
        for movie in Movie.objects.filter(depot=self, alternative=None):
            if movie.update_needed:
                movie.update()


class Alternative(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name="alternatives")

    class Meta:
        unique_together = ("depot", "name")

    def __str__(self):
        return "{}".format(self.name)

    # getters
    def get_movie(self):
        return self.movies.get(depot=self.depot, alternative=self)


class Value(models.Model):
    alternative = models.ForeignKey(Alternative, related_name="values", on_delete=models.CASCADE)
    date = models.DateField()
    value = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ("alternative", "date")

    def __str__(self):
        return "{} {} {}".format(self.alternative, self.get_date(), self.value)

    # getters
    def get_date(self):
        return self.date.strftime("%d.%m.%Y")


class Flow(models.Model):
    alternative = models.ForeignKey(Alternative, related_name="flows", on_delete=models.CASCADE)
    date = models.DateField()
    value = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(0.01)])
    flow = models.DecimalField(decimal_places=2, max_digits=15)

    class Meta:
        unique_together = ("alternative", "date")

    def __str__(self):
        return "{} {} {}".format(self.alternative, self.get_date(), self.flow)

    # getters
    def get_date(self):
        return self.date.strftime("%d.%m.%Y")


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
    alternative = models.ForeignKey(Alternative, blank=True, null=True, related_name="movies", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("depot", "alternative")

    def __str__(self):
        text = "{} {}".format(self.depot, self.alternative).replace(" None", "")
        return text

    # getters
    @staticmethod
    def get_percentage(value):
        if type(value) is float or type(value) is Decimal:
            return str(value * 100) + " %"
        return value

    def get_df(self, timespan=None):
        if timespan and timespan.start_date and timespan.end_date:
            pictures = self.pictures.filter(d__gte=timespan.start_date,
                                            d__lte=timespan.end_date)
        else:
            pictures = self.pictures
        pictures = pictures.order_by("d")
        pictures = pictures.values("d", "v", "g", "cr", "twr", "cs", "f")
        df = pd.DataFrame(list(pictures), dtype=np.float64)
        if df.empty:
            return pd.DataFrame(columns=["d", "v", "g", "cr", "twr", "cs", "f"])
        df.set_index("d", inplace=True)
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
        data["v"] = (pictures.values_list("v", flat=True))
        data["f"] = (pictures.values_list("f", flat=True))
        data["g"] = (pictures.values_list("g", flat=True))
        data["cr"] = (pictures.values_list("cr", flat=True))
        data["twr"] = (pictures.values_list("twr", flat=True))
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
                data[key] = "x"

            if data[key] == "x":
                pass
            elif key in ["cr", "twr"]:
                data[key] = "{} %".format(round(data[key] * 100, 2))
            else:
                data[key] = "{} {}".format(round(data[key], 2), user.get_currency_display())

        return data

    # init
    @staticmethod
    def init_movies(sender, instance, **kwargs):
        if sender is Alternative:
            depot = instance.depot
            Movie.objects.get_or_create(depot=depot, alternative=instance)
        elif sender is Depot:
            depot = instance
            Movie.objects.get_or_create(depot=depot, alternative=None)

    @staticmethod
    def init_update(sender, instance, **kwargs):
        if sender is (Value or Flow):
            q1 = Q(alternative=instance.alternative)
            q2 = Q(depot=instance.alternative.depot, alternative=None)
            movies = Movie.objects.filter(q1 | q2)
            movies.update(update_needed=True)

    # update
    def update(self):
        if self.alternative:
            df = self.calc_alternative()
        elif not self.alternative:
            df = self.calc_depot()
        else:
            raise Exception("Depot or alternative must be defined in a movie.")

        old_df = self.get_df()

        if old_df.equals(df.iloc[:len(old_df)]):
            df = df.iloc[len(old_df):]
        else:
            self.pictures.all().delete()

        pictures = list()
        for index, row in df.iterrows():
            picture = Picture(
                movie=self,
                d=index,
                v=row["v"],
                f=row["f"],
                cs=row["cs"],
                g=row["g"],
                cr=row["cr"],
                twr=row["twr"]
            )
            pictures.append(picture)
        Picture.objects.bulk_create(pictures)

        self.update_needed = False
        self.save()

    @staticmethod
    def calc_fifo(value, flow):
        """
        The alternative has a value and after that occurs a flow. The cs is before the flow occurs.
        """
        assert len(value) == len(flow)
        cs = list()
        cs.append(0)
        cs.append(flow[0])
        for i in range(1, len(value) - 1):
            if flow[i] < 0:
                cs.append(cs[-1] * (1 + flow[i] / value[i]))
            elif flow[i] > 0:
                cs.append(cs[-1] + flow[i])
            else:
                cs.append(cs[-1])
        return cs

    def calc_alternative(self):
        """
        The alternative has some properties. For example, it has a cr or a g. These properties apply before the flow
        applies. Therefore you make a gain of 10 whatever and afterwards there is a flow in or out of this alternative.
        """
        # values
        values = Value.objects.filter(alternative=self.alternative)
        values = values.values("date", "value")
        values_df = pd.DataFrame(list(values), columns=["date", "value"], dtype=np.float64)
        # flows
        flows = Flow.objects.filter(alternative=self.alternative)
        flows = flows.values("date", "flow", "value")
        flows_df = pd.DataFrame(list(flows), columns=["date", "flow", "value"], dtype=np.float64)
        # df
        df = pd.concat([values_df, flows_df], sort=False)
        if df.empty:
            return df
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)
        date_series = pd.date_range(start=df.index[0], end=timezone.now().date())
        df = df.reindex(date_series)
        df.loc[:, "f"] = df.loc[:, "flow"].fillna(0)
        df.loc[:, "v"] = df.loc[:, "value"].ffill()
        # cs
        df.loc[:, "cs"] = Movie.calc_fifo(df.loc[:, "v"].tolist(), df.loc[:, "f"].tolist())
        # g
        df.loc[:, "g"] = df.loc[:, "v"] - df.loc[:, "cs"]
        # cr
        df.loc[:, "cr"] = df.loc[:, "v"] / df.loc[:, "cs"]
        df.loc[:, "cr"] = df.loc[:, "cr"].fillna(1)
        df.loc[:, "cr"] = df.loc[:, "cr"] - 1
        # ttwr
        df.loc[:, "twr"] = df.loc[:, "v"] / (df.loc[:, "v"].shift(1) + df.loc[:, "f"].shift(1))
        df.loc[:, "twr"] = df.loc[:, "twr"].fillna(1)
        df.loc[:, "twr"] = df.loc[:, "twr"].cumprod()
        df.loc[:, "twr"] = df.loc[:, "twr"] - 1
        # return
        df = df.loc[:, ["v", "f", "cs", "g", "cr", "twr"]]
        df.loc[:, ["v", "f", "cs", "g"]] = df.loc[:, ["v", "f", "cs", "g"]].applymap(lambda x: round(x, 2))
        df.loc[:, ["cr", "twr"]] = df.loc[:, ["cr", "twr"]].applymap(lambda x: round(x, 4))
        return df

    def calc_depot(self):
        """
        The DEPOT has some properties. For example, it has a cr or a g. These properties apply before the flow
        applies. Therefore you make a gain of 10 whatever and afterwards there is a flow in or out of this alternative.
        """
        df = pd.DataFrame(columns=["v", "f"], dtype=np.float64)
        # alternatives
        alternatives = list()
        for alternative in self.depot.alternatives.all().select_related("depot"):
            alternative_df = alternative.get_movie().get_df()
            alternative_df = alternative_df.loc[:, ["v", "f"]]
            alternative_df.rename(columns={"v": alternative.slug + "__v", "f": alternative.slug + "__f"}, inplace=True)
            alternatives.append(alternative.slug)
            df = pd.concat([df, alternative_df], axis=1, sort=False)
        # all together
        if df.empty:
            return df
        df.sort_index(inplace=True)
        # sum it up
        df.loc[:, "v"] = df.loc[:, [slug + "__v" for slug in alternatives]].sum(axis=1, skipna=True)
        df.loc[:, "f"] = df.loc[:, [slug + "__f" for slug in alternatives]].sum(axis=1, skipna=True)
        # cs
        df.loc[:, "cs"] = Movie.calc_fifo(df.loc[:, "v"].tolist(), df.loc[:, "f"].tolist())
        # g
        df.loc[:, "g"] = df.loc[:, "v"] - df.loc[:, "cs"]
        # cr
        df.loc[:, "cr"] = df.loc[:, "v"] / df.loc[:, "cs"]
        df.loc[:, "cr"] = df.loc[:, "cr"].fillna(1)
        df.loc[:, "cr"] = df.loc[:, "cr"] - 1
        # ttwr
        df.loc[:, "twr"] = df.loc[:, "v"] / (df.loc[:, "v"].shift(1) + df.loc[:, "f"].shift(1))
        df.loc[:, "twr"] = df.loc[:, "twr"].fillna(1)
        df.loc[:, "twr"] = df.loc[:, "twr"].cumprod()
        df.loc[:, "twr"] = df.loc[:, "twr"] - 1
        print_df(df)
        # return
        df = df.loc[:, ["v", "f", "cs", "g", "cr", "twr"]]
        df.loc[:, ["v", "f", "cs", "g"]] = df.loc[:, ["v", "f", "cs", "g"]].applymap(lambda x: round(x, 2))
        df.loc[:, ["cr", "twr"]] = df.loc[:, ["cr", "twr"]].applymap(lambda x: round(x, 4))
        return df


class Picture(models.Model):
    movie = models.ForeignKey(Movie, related_name="pictures", on_delete=models.CASCADE)
    d = models.DateField()

    v = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=2)
    f = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=2)
    g = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=2)
    cr = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=4)
    twr = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=4)
    cs = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=2)

    def __str__(self):
        return "{} {} {} {}".format(self.movie, self.d, self.v, self.f)


post_save.connect(Movie.init_update, sender=Value)
post_delete.connect(Movie.init_update, sender=Value)
post_save.connect(Movie.init_update, sender=Flow)
post_delete.connect(Movie.init_update, sender=Flow)
post_save.connect(Movie.init_movies, sender=Alternative)
post_save.connect(Movie.init_movies, sender=Depot)
