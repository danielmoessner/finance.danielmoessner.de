from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.functional import cached_property

from finance.core.utils import create_slug_on_username


class StandardUser(AbstractUser):
    slug = models.SlugField(unique=True)
    DATE_FORMAT_CHOICES = (
        ("%d.%m.%Y", "Date.Month.Year"),
        ("%m/%d/%Y", "Month/Date/Year"),
    )
    date_format = models.CharField(max_length=8, choices=DATE_FORMAT_CHOICES)
    CURRENCY_CHOICES = (
        ("€", "EUR"),
        ("$", "USD"),
    )
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    rounded_numbers = models.BooleanField(default=True)
    # banking settings
    banking_active = models.BooleanField(default=False)  # not used at the moment

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.slug:
            self.slug = create_slug_on_username(self)
        super(StandardUser, self).save(force_insert, force_update, using, update_fields)

    # getters
    @cached_property
    def get_rounded_numbers(self):
        return self.rounded_numbers

    # setters
    def set_banking_depot_active(self, depot):
        self.banking_depots.update(is_active=False)
        depot.is_active = True
        depot.save()

    def set_crypto_depot_active(self, depot):
        for d in self.crypto_depots.exclude(depot):
            d.is_active = False
            d.save()
        depot.is_active = True
        depot.save()
