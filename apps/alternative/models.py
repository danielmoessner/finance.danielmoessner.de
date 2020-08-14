from django.db.models.signals import post_save, post_delete
from django.core.validators import MinValueValidator
from django.db.models import Q
from django.utils import timezone
from django.db import models

from apps.users.models import StandardUser
from apps.core.models import Timespan as CoreTimespan
from apps.core.models import Depot as CoreDepot
import apps.core.return_calculation as rc
import apps.core.duplicated_code as dc
import apps.core.utils as utils

import pandas as pd
import numpy as np


class Depot(CoreDepot):
    user = models.ForeignKey(StandardUser, editable=False, related_name="alternative_depots", on_delete=models.CASCADE)
    # query optimization
    latest_picture = models.ForeignKey('Picture', on_delete=models.SET_NULL, blank=True, null=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save(force_insert=force_insert, force_update=force_update, using=using,
                     update_fields=update_fields)
        if self.is_active:
            self.user.alternative_depots.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)

    # getters
    def get_flow_df(self):
        # instantiate a new dataframe
        df = pd.DataFrame(columns=['date', 'flow'])
        df.set_index('date', inplace=True)
        # merge the dataframe with all allternative dataframes
        for alternative in list(self.alternatives.all()):
            alternative_df = alternative.get_flow_df()
            if alternative_df is None:
                continue
            alternative_df.rename(columns={'flow': 'flow__' + str(alternative.pk)}, inplace=True)
            df = df.merge(alternative_df, how='outer', on='date', sort=True)
        # return none if the df is empty
        if df.empty:
            return None
        # sum up all the flows
        df = utils.sum_up_columns_in_a_dataframe(df, 'flow')
        # return the df
        return df

    def get_value_df(self):
        # get the df with all values
        df = utils.get_merged_value_df_from_queryset(self.alternatives.all())
        # sums up all the values of the assets and interpolates
        df = utils.sum_up_columns_in_a_dataframe(df)
        # return the new df
        return df

    def get_movie(self):
        movie, created = Movie.objects.get_or_create(depot=self, alternative=None)
        if movie.update_needed:
            movie.update()
        return movie

    # movies
    def reset_movies(self, delete=False):
        if delete:
            self.movies.all().delete()

        for alternative in self.alternatives.all():
            Movie.objects.get_or_create(depot=self, alternative=alternative)
        Movie.objects.get_or_create(depot=self, alternative=None)


class Alternative(models.Model):
    name = models.CharField(max_length=200)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name="alternatives")
    # query optimization
    latest_picture = models.ForeignKey('Picture', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        unique_together = ("depot", "name")

    def __str__(self):
        return '{}'.format(self.name)

    # getters
    def get_value_df(self):
        df = pd.DataFrame(list(self.values.all().values('date', 'value')), columns=['date', 'value'])
        df.set_index('date', inplace=True)
        # return none if the df is empty
        if df.empty:
            return None
        # standardize the numbers
        df.loc[:, 'value'] = pd.to_numeric(df.loc[:, 'value'])
        # change the time
        # df = utils.change_time_of_date_index_in_df(df, 13)
        # group by time and sum up the values for the day
        df = df.groupby(df.index, sort=True).tail(1)
        # return the df
        return df

    def get_flow_df(self):
        df = pd.DataFrame(list(self.flows.all().values('date', 'flow')), columns=['date', 'flow'])
        df.set_index('date', inplace=True)
        # return none if the df is empty
        if df.empty:
            return None
        # standardize the numbers
        df.loc[:, 'flow'] = pd.to_numeric(df.loc[:, 'flow'], downcast='float')
        # change the time
        # df = utils.change_time_of_date_index_in_df(df, 12)
        # group by time and sum up the values for the day
        df = df.groupby(df.index, sort=True).sum()
        # return the df
        return df

    def get_flows_and_values(self):
        flows = list(self.flows.all().values('date', 'flow', 'pk'))
        values = list(self.values.all().values('date', 'value', 'pk'))
        flows_and_values = flows + values
        flows_and_values_sorted = sorted(flows_and_values, key=lambda k: k['date'])
        return flows_and_values_sorted

    def get_movie(self):
        movie, created = Movie.objects.get_or_create(depot=self.depot, alternative=self)
        if movie.update_needed:
            movie.update()
        return movie

    def get_latest_picture(self):
        return dc.get_latest_picture(self)


class Value(models.Model):
    alternative = models.ForeignKey(Alternative, related_name="values", on_delete=models.CASCADE)
    date = models.DateTimeField()
    value = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ("alternative", "date")

    def __str__(self):
        return '{}: {} {}'.format(self.alternative, timezone.localtime(self.date).strftime('%d.%m.%y %H:%M'),
                                  self.value)


class Flow(models.Model):
    alternative = models.ForeignKey(Alternative, related_name="flows", on_delete=models.CASCADE)
    date = models.DateTimeField()
    flow = models.DecimalField(decimal_places=2, max_digits=15)

    class Meta:
        unique_together = ("alternative", "date")

    def __str__(self):
        return '{}: {} {}'.format(self.alternative, timezone.localtime(self.date).strftime('%d.%m.%y %H:%M'), self.flow)


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
        if self.alternative is None and self.depot:
            self.flow_df = self.depot.get_flow_df()
            self.value_df = self.depot.get_value_df()
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
        # check to avoid errors with db queries
        # if np.isnan(time_weighted_return):
        #     time_weighted_return = None
        # set the value
        self.time_weighted_return = time_weighted_return

    def calc_internal_rate_of_return(self):
        # get the value
        print(self.flow_df)
        print(self.value_df)
        internal_rate_of_return_df = rc.get_internal_rate_of_return_df(self.flow_df, self.value_df)
        internal_rate_of_return = rc.get_internal_rate_of_return(internal_rate_of_return_df)
        # check to avoid errors with db queries
        # if np.isnan(internal_rate_of_return):
        #     internal_rate_of_return = None
        # set the value
        self.internal_rate_of_return = internal_rate_of_return

    def calc_current_return(self):
        # get the value
        current_return_df = rc.get_current_return_df(self.flow_df, self.value_df)
        current_return = rc.get_current_return(current_return_df)
        # check to avoid errors with db queries
        # if np.isnan(current_return):
        #     current_return = None
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
                              date=index, value=row['value'], flow=row['flow'])
            pictures.append(picture)
        Picture.objects.bulk_create(pictures)

    # getters
    def get_stats(self):
        return {
            'Time Weighted Return': utils.round_value_if_exists(self.time_weighted_return),
            'Current Return': utils.round_value_if_exists(self.current_return),
            'Internal Rate of Return': utils.round_value_if_exists(self.internal_rate_of_return)
        }

    def get_pictures(self):
        pictures = list(self.pictures.all().values('date', 'invested_capital', 'value', 'profit', 'flow'))
        pictures = sorted(pictures, key=lambda k: k['date'])
        return pictures

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
