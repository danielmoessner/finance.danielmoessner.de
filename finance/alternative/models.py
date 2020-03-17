from django.db.models.signals import post_save, post_delete
from django.core.validators import MinValueValidator
from django.db.models import Q
from django.utils import timezone
from django.db import models

from finance.users.models import StandardUser
from finance.core.models import Timespan as CoreTimespan
from finance.core.models import Depot as CoreDepot
import finance.core.return_calculation as rc
import finance.core.utils as utils

from decimal import Decimal
import pandas as pd
import numpy as np


def init_alternative(user):
    from finance.alternative.forms import ValueForm
    from finance.alternative.forms import FlowForm
    from finance.core.utils import create_slug
    from django.utils import timezone
    from datetime import timedelta
    depot = Depot.objects.create(name="Test Depot", user=user)
    user.set_alternative_depot_active(depot)
    # account
    alternative1 = Alternative(depot=depot, name="Old-Timer")
    alternative1.slug = create_slug(alternative1)
    alternative1.save()
    alternative2 = Alternative(depot=depot, name="Black-Watch")
    alternative2.slug = create_slug(alternative1)
    alternative2.save()
    alternative3 = Alternative(depot=depot, name="Tube Amplifier")
    alternative3.slug = create_slug(alternative1)
    alternative3.save()
    # flows
    date = (timezone.now() - timedelta(days=30))
    flow = FlowForm(depot, {"alternative": alternative1.pk, "date": date.strftime("%Y-%m-%dT%H:%M"), "value": 0,
                            "flow": 10000})
    flow.save()
    date = (timezone.now() - timedelta(days=40))
    flow = FlowForm(depot,
                    {"alternative": alternative2.pk, "date": date.strftime("%Y-%m-%dT%H:%M"), "value": 0, "flow": 3000})
    flow.save()
    date = (timezone.now() - timedelta(days=60))
    flow = FlowForm(depot,
                    {"alternative": alternative3.pk, "date": date.strftime("%Y-%m-%dT%H:%M"), "value": 0, "flow": 1500})
    flow.save()
    date = (timezone.now() - timedelta(days=20))
    flow = FlowForm(depot, {"alternative": alternative3.pk, "date": date.strftime("%Y-%m-%dT%H:%M"), "value": 1600,
                            "flow": 400})
    flow.save()
    # values
    date = (timezone.now() - timedelta(days=25))
    value = ValueForm(depot, {"alternative": alternative1.pk, "date": date.strftime("%Y-%m-%dT%H:%M"), "value": 9990})
    value.save()
    date = (timezone.now() - timedelta(days=25))
    value = ValueForm(depot, {"alternative": alternative2.pk, "date": date.strftime("%Y-%m-%dT%H:%M"), "value": 3000})
    value.save()
    date = (timezone.now() - timedelta(days=25))
    value = ValueForm(depot, {"alternative": alternative3.pk, "date": date.strftime("%Y-%m-%dT%H:%M"), "value": 2300})
    value.save()
    date = (timezone.now() - timedelta(days=5))
    value = ValueForm(depot, {"alternative": alternative1.pk, "date": date.strftime("%Y-%m-%dT%H:%M"), "value": 10050})
    value.save()
    date = (timezone.now() - timedelta(days=5))
    value = ValueForm(depot, {"alternative": alternative2.pk, "date": date.strftime("%Y-%m-%dT%H:%M"), "value": 3000})
    value.save()
    date = (timezone.now() - timedelta(days=5))
    value = ValueForm(depot, {"alternative": alternative3.pk, "date": date.strftime("%Y-%m-%dT%H:%M"), "value": 2300})
    value.save()
    # timespan
    Timespan.objects.create(depot=depot, name="Default Timespan", start_date=None, end_date=None, is_active=True)
    # movies
    depot.reset_movies()


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
        return '{}'.format(self.name)

    # getters
    def get_value_df(self):
        df = pd.DataFrame(list(self.values.all().values('date', 'value')))
        df.loc[:, 'value'] = pd.to_numeric(df.loc[:, 'value'])
        return df

    def get_flow_df(self):
        df = pd.DataFrame(list(self.flows.all().values('date', 'flow')))
        df.loc[:, 'flow'] = pd.to_numeric(df.loc[:, 'flow'])
        return df

    def get_flows_and_values(self):
        flows = list(self.flows.all().values('date', 'flow', 'pk'))
        values = list(self.values.all().values('date', 'value', 'pk'))
        flows_and_values = flows + values
        flows_and_values_sorted = sorted(flows_and_values, key=lambda k: k['date'])
        return flows_and_values_sorted

    def get_pictures(self):
        pictures = list(self.get_movie().pictures.all().values('date', 'invested_capital', 'value', 'profit', 'flow'))
        pictures = sorted(pictures, key=lambda k: k['date'])
        return pictures

    def get_movie(self):
        movie, created = Movie.objects.get_or_create(depot=self.depot, alternative=self)
        if movie.update_needed:
            movie.update()
        return movie

    def get_stats(self):
        movie, created = Movie.objects.get_or_create(alternative=self, depot=self.depot)
        if movie.update_needed:
            movie.update()
        return [
            ['Time Weighted Return', utils.round_value_if_exists(movie.time_weighted_return)],
            ['Current Return', utils.round_value_if_exists(movie.current_return)],
            ['Internal Rate of Return', utils.round_value_if_exists(movie.internal_rate_of_return)]
        ]


class Value(models.Model):
    alternative = models.ForeignKey(Alternative, related_name="values", on_delete=models.CASCADE)
    date = models.DateTimeField()
    value = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ("alternative", "date")


class Flow(models.Model):
    alternative = models.ForeignKey(Alternative, related_name="flows", on_delete=models.CASCADE)
    date = models.DateTimeField()
    flow = models.DecimalField(decimal_places=2, max_digits=15)

    class Meta:
        unique_together = ("alternative", "date")


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
    depot = models.ForeignKey(Depot, blank=True, null=True, related_name="movies", on_delete=models.CASCADE)
    alternative = models.ForeignKey(Alternative, blank=True, null=True, related_name="movies", on_delete=models.CASCADE)
    time_weighted_return = models.DecimalField(blank=True, null=True, max_digits=8, decimal_places=2)
    internal_rate_of_return = models.DecimalField(blank=True, null=True, max_digits=8, decimal_places=2)
    current_return = models.DecimalField(blank=True, null=True, max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ("depot", "alternative")

    def update(self):
        # get the dfs
        if self.alternative and self.depot:
            self.flow_df = self.alternative.get_flow_df()
            self.value_df = self.alternative.get_value_df()
        # reset
        self.reset_data()
        # calculate the new data
        self.calc_pictures()
        self.calc_time_weighted_return()
        self.calc_internal_rate_of_return()
        self.calc_current_return()
        # save
        self.save()

    def reset_data(self):
        # delete old pictures
        self.pictures.all().delete()
        # set values to None
        self.internal_rate_of_return = None
        self.time_weighted_return = None
        self.current_return = None
        # set updated need to false
        self.update_needed = False

    def calc_time_weighted_return(self):
        # get the value
        time_weighted_return_df = rc.get_time_weighted_return_df(self.flow_df, self.value_df)
        time_weighted_return = rc.get_time_weighted_return(time_weighted_return_df)
        print(time_weighted_return)
        # check to avoid errors with db queries
        if np.isnan(time_weighted_return):
            time_weighted_return = None
        # set the value
        self.time_weighted_return = time_weighted_return

    def calc_internal_rate_of_return(self):
        # get the value
        internal_rate_of_return_df = rc.get_internal_rate_of_return_df(self.flow_df, self.value_df)
        internal_rate_of_return = rc.get_internal_rate_of_return(internal_rate_of_return_df)
        # check to avoid errors with db queries
        if np.isnan(internal_rate_of_return):
            internal_rate_of_return = None
        # set the value
        self.internal_rate_of_return = internal_rate_of_return

    def calc_current_return(self):
        # get the value
        current_return_df = rc.get_current_return_df(self.flow_df, self.value_df)
        current_return = rc.get_current_return(current_return_df)
        # check to avoid errors with db queries
        if np.isnan(current_return):
            current_return = None
        # set the value
        self.current_return = current_return

    def calc_pictures(self):
        # get the df
        df = rc.get_current_return_df(self.flow_df, self.value_df)
        # don't run calculations if the data is not complete
        if df is None:
            return
        # calculate profit
        df.loc[:, 'profit'] = df.loc[:, 'value'] - df.loc[:, 'invested_capital']
        # create all pictures
        pictures = []
        for index, row in df.iterrows():
            picture = Picture(movie=self, invested_capital=row['invested_capital'], profit=row['profit'],
                              date=row['date'], value=row['value'], flow=row['flow'])
            pictures.append(picture)
        Picture.objects.bulk_create(pictures)

    # getters
    @staticmethod
    def get_percentage(value):
        if type(value) is float or type(value) is Decimal:
            return str(value * 100) + " %"
        return value

    # init
    @staticmethod
    def init_update(sender, instance, **kwargs):
        if sender is Value or sender is Flow:
            q1 = Q(depot=instance.alternative.depot, alternative=instance.alternative)
            q2 = Q(depot=instance.alternative.depot, alternative=None)
            movies = Movie.objects.filter(q1 | q2)
            movies.update(update_needed=True)


class Picture(models.Model):
    movie = models.ForeignKey(Movie, related_name="pictures", on_delete=models.CASCADE)
    date = models.DateTimeField()
    value = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=2)
    invested_capital = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=2)
    profit = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=2)
    flow = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=2)


post_save.connect(Movie.init_update, sender=Value)
post_delete.connect(Movie.init_update, sender=Value)
post_save.connect(Movie.init_update, sender=Flow)
post_delete.connect(Movie.init_update, sender=Flow)
