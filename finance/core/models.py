from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from finance.core.utils import create_slug
from datetime import timedelta


class IntelligentTimespan(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateTimeField(blank=True, null=True)
    period = models.DurationField(blank=True, null=True)  # remove later
    end_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.name)

    # getters
    def get_timespans_data(self, movie, keys):
        timespans = self.get_timespans()
        data = list()
        for timespan in timespans:
            timespan_data = dict()
            timespan_data["start_date"] = timespan.start_date.strftime(self.user.date_format)
            timespan_data["end_date"] = (timespan.end_date - timedelta(days=1)) \
                .strftime(self.user.date_format)
            timespan_number_data = timespan.get_data(movie, keys)
            timespan_data.update(timespan_number_data)
            if all([timespan_data[key] is not None and timespan_data[key] != 0 for key in keys]):
                data.append(timespan_data)
        return data

    def get_data(self, movie, keys):
        try:
            start_picture = movie.pictures.filter(d__lte=self.start_date).latest("d")
        except ObjectDoesNotExist:
            start_picture = None
        try:
            end_picture = movie.pictures.filter(d__lte=self.end_date).latest("d")
        except ObjectDoesNotExist:
            end_picture = None

        data = list()
        for key in keys:
            key_data = dict()
            key_data["start_date"] = self.start_date.strftime(self.depot.user.date_format)
            key_data["end_date"] = self.end_date.strftime(self.depot.user.date_format)
            if start_picture is None and end_picture is None:
                key_data[key] = None
            elif start_picture is None:
                key_data[key] = getattr(end_picture, key)
            else:
                key_data[key] = getattr(end_picture, key) - getattr(start_picture, key)
            data.append(key_data)
        return data

    @staticmethod
    def get_default_intelligent_timespan():
        pts, created = IntelligentTimespan.objects.get_or_create(
            name="Default Timespan", start_date=None, end_date=None)
        return pts


class Timespan(models.Model):
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(Timespan, self).__init__(*args, **kwargs)
        self.ts = None

    # getters
    def get_data(self, movie, keys):
        # new approach
        start_pictures = movie.pictures.filter(d__lte=self.start_date)
        end_pictures = movie.pictures.filter(d__lte=self.end_date)
        try:
            start_picture = start_pictures.latest("d")
        except ObjectDoesNotExist:
            start_picture = None
        try:
            end_picture = end_pictures.latest("d")
        except ObjectDoesNotExist:
            end_picture = None

        data = dict()
        for key in keys:
            if start_picture is None and end_picture is None:
                data[key] = None
            elif start_picture is None:
                data[key] = getattr(end_picture, key)
            else:
                data[key] = getattr(end_picture, key) - getattr(start_picture, key)
        return data

        # old approach
        # movie_data = movie.get_data()
        # start = None
        # end = len(movie_data["d"]) - 1
        # for i in range(len(movie_data["d"])):
        #     if self.start_date <= movie_data["d"][i] and start is None:
        #         start = i - 1
        #     if self.end_date <= movie_data["d"][i]:
        #         end = i - 1
        #         break
        # for dict_key in dict_keys:
        #     if (start == end) or (end == -1) or (start is None):
        #         data[dict_key] = None
        #     if start == -1:
        #         data[dict_key] = round(movie_data[dict_key][end], 2)
        #     else:
        #       data[dict_key] = round(movie_data[dict_key][end] - movie_data[dict_key][start], 2)


class Depot(models.Model):
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Account(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.slug:
            self.slug = create_slug(self)
        super(Account, self).save(force_insert, force_update, using, update_fields)
