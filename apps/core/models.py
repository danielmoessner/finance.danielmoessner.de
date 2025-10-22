from django.db import models


class Depot(models.Model):
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Account(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
