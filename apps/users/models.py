from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db import models

from apps.core.utils import create_slug

from datetime import timedelta
import random


class StandardUser(AbstractUser):
    slug = models.SlugField(unique=True)
    # general
    DATE_FORMAT_CHOICES = (
        ("%d.%m.%Y", "Date.Month.Year"),
        ("%m/%d/%Y", "Month/Date/Year"),
    )
    date_format = models.CharField(max_length=8, choices=DATE_FORMAT_CHOICES)
    FRONT_PAGE_CHOICES = (
        ("BANKING", "Banking"),
        ("CRYPTO", "Crypto"),
        ("SETTINGS", "Settings")
    )
    front_page = models.CharField(max_length=8, choices=FRONT_PAGE_CHOICES, default="SETTINGS")
    rounded_numbers = models.BooleanField(default=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.slug:
            self.slug = create_slug(self, on=self.username)
        super(StandardUser, self).save(force_insert, force_update, using, update_fields)

    # getters
    def get_active_banking_depot_pk(self):
        depots = self.banking_depots.filter(is_active=True)
        if depots.count() <= 0:
            return None
        return depots.first().pk

    def get_active_alternative_depot_pk(self):
        depots = self.alternative_depots.filter(is_active=True)
        if depots.count() <= 0:
            return None
        return depots.first().pk

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
        from apps.banking.models import Account, Category, Depot, Change
        name = 'Depot {}'.format(random.randrange(100, 999))
        depot = Depot.objects.create(name=name, user=self)
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
        # return the depot that was created and contains the test data
        return depot

    def create_random_alternative_data(self):
        from apps.alternative.models import Depot, Alternative, Value, Flow
        from apps.alternative.forms import ValueForm, FlowForm
        from apps.core.utils import create_slug
        from django.utils import timezone
        from datetime import timedelta
        name = 'Depot {}'.format(random.randrange(100, 999))
        depot = Depot.objects.create(name=name, user=self)
        self.set_alternative_depot_active(depot)

        # helper create alternative
        def create_alternative(name):
            alternative = Alternative(depot=depot, name=name)
            alternative.slug = create_slug(alternative)
            alternative.save()
            return alternative

        # helper create flow
        def create_flow(alternative, days_before_now, flow_flow):
            date = (timezone.now().replace(hour=00, minute=00) - timedelta(days=days_before_now, hours=13))
            flow = FlowForm(depot, {"alternative": alternative.pk, "date": date, "flow": flow_flow})
            flow.save()
            return flow

        # helper create value
        def create_value(alternative, days_before_now, value_value):
            date = (timezone.now().replace(hour=00, minute=00) - timedelta(days=days_before_now, hours=12))
            value = ValueForm(depot, {"alternative": alternative.pk, "date": date, "value": value_value})
            value.save()
            return value

        # alternatives
        alternative1 = create_alternative("Old-Timer")
        alternative2 = create_alternative('Black-Watch')
        alternative3 = create_alternative('Tube Amplifier')

        # 1
        create_flow(alternative1, 50, 100)
        create_value(alternative1, 50, 100)
        create_value(alternative1, 30, 110)
        create_flow(alternative1, 20, 50)
        create_value(alternative1, 20, 160)
        create_value(alternative1, 0, 160)
        # 2
        create_flow(alternative2, 40, 100)
        create_value(alternative2, 40, 100)
        create_value(alternative2, 0, 200)
        # 3
        create_flow(alternative3, 30, 100)
        create_value(alternative3, 30, 100)
        create_value(alternative3, 20, 50)
        create_flow(alternative3, 10, 10)
        create_value(alternative3, 10, 60)
        create_value(alternative3, 0, 60)

        # return the depot that contains all the test data
        return depot
