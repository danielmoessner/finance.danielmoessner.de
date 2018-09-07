from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse_lazy

from finance.core.utils import create_slug


class StandardUser(AbstractUser):
    slug = models.SlugField(unique=True)
    # general
    DATE_FORMAT_CHOICES = (
        ("%d.%m.%Y", "Date.Month.Year"),
        ("%m/%d/%Y", "Month/Date/Year"),
    )
    date_format = models.CharField(max_length=8, choices=DATE_FORMAT_CHOICES)
    CURRENCY_CHOICES = (
        ("EUR", "€"),
        ("USD", "$"),
    )
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    banking_url = reverse_lazy("banking:index", kwargs={})
    crypto_url = reverse_lazy("crypto:index", kwargs={})
    settings_url = reverse_lazy("users:settings", kwargs={})
    FRONT_PAGE_CHOICES = (
        ("BANKING", "Banking"),
        ("CRYPTO", "Crypto"),
        ("SETTINGS", "Settings")
    )
    front_page = models.CharField(max_length=8, choices=FRONT_PAGE_CHOICES, default="SETTINGS")
    # crypto
    crypto_is_active = models.BooleanField(default=False)
    rounded_numbers = models.BooleanField(default=True)
    # banking
    banking_is_active = models.BooleanField(default=False)
    # alternative
    alternative_is_active = models.BooleanField(default=False)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.slug:
            self.slug = create_slug(self, on=self.username)
        super(StandardUser, self).save(force_insert, force_update, using, update_fields)

    # setters
    def set_banking_depot_active(self, depot):
        self.banking_depots.update(is_active=False)
        depot.is_active = True
        depot.save()

    def set_crypto_depot_active(self, depot):
        self.crypto_depots.update(is_active=False)
        depot.is_active = True
        depot.save()

    def set_alternative_depot_active(self, depot):
        self.alternative_depots.update(is_active=False)
        depot.is_active = True
        depot.save()
