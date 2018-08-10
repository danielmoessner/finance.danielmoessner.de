from django.utils import timezone
from django.db import models


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

    # getters
    @staticmethod
    def get_default_intelligent_timespan():  # this is useless but cant remove it cuz of migrations
        pts, created = Timespan.objects.get_or_create(
            name="Default Timespan", start_date=None, end_date=None)
        return pts


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
