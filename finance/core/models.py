from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from finance.core.utils import create_slug


class Timespan(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateTimeField(blank=True, null=True)
    period = models.DurationField(blank=True, null=True)  # remove later
    end_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.name)

    @staticmethod
    def get_default_intelligent_timespan():  # this is useless but cant remove it cuz of migrations
        pts, created = Timespan.objects.get_or_create(
            name="Default Timespan", start_date=None, end_date=None)
        return pts

    # getters
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
