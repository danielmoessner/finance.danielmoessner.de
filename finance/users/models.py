from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.urls import reverse_lazy
from django.db import models
from datetime import timedelta
import random

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

    # create
    def create_random_banking_data(self):
        from finance.banking.models import Account, Category, Depot, Change, Timespan, Movie, Picture
        depot = Depot.objects.create(name="Random Depot", user=self)
        self.set_banking_depot_active(depot)
        # account
        account1 = Account(depot=depot, name="Bank #1")
        account1.slug = create_slug(account1)
        account1.save()
        account2 = Account.objects.create(depot=depot, name="Bank #2")
        account2.slug = create_slug(account1)
        account2.save()
        # category
        category1 = Category.objects.create(depot=depot, name="Category #1",
                                            description="This category is for test purposes only.")
        category1.slug = create_slug(category1)
        category1.save()
        category2 = Category.objects.create(depot=depot, name="Category #2",
                                            description="This category is for test purposes only.")
        category2.slug = create_slug(category2)
        category2.save()
        category3 = Category.objects.create(depot=depot, name="Category #3",
                                            description="This category is for test purposes only.")
        category3.slug = create_slug(category3)
        category3.save()
        # changes
        changes = list()
        for i in range(0, 20):
            random_number = random.randint(1, 2)
            account = account1 if random_number == 1 else account2
            random_number = random.randint(1, 3)
            category = category1 if random_number == 1 else category2 if random_number == 2 \
                else category3
            random_number = random.randint(-400, 600)
            change = random_number
            random_number = random.randint(1, 90)
            date = timezone.now() - timedelta(days=random_number)
            description = "Change #{}".format(i)
            changes.append(Change(account=account, category=category, change=change, date=date,
                                  description=description))
        Change.objects.bulk_create(changes)
        # timespan
        Timespan.objects.create(depot=depot, name="Default Timespan", start_date=None, end_date=None, is_active=True)
        # movies
        depot.reset_movies()
