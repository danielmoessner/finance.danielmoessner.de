from typing import TYPE_CHECKING

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.users.models import StandardUser

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from apps.alternative.models import Alternative
    from apps.banking.models import Account
    from apps.crypto.models import Asset
    from apps.stocks.models import Stock


class Bucket(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        StandardUser, on_delete=models.CASCADE, related_name="buckets"
    )
    wanted_percentage = models.FloatField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    if TYPE_CHECKING:
        banking_items: QuerySet["Account"]
        crypto_items: QuerySet["Asset"]
        alternative_items: QuerySet["Alternative"]
        stocks_items: QuerySet["Stock"]

    @property
    def wanted_percentage_str(self) -> str:
        return "{:,.2f} %".format(self.wanted_percentage)

    def __str__(self):
        return self.name

    def get_items(self):
        i1 = self.banking_items.all()
        i2 = self.crypto_items.all()
        i3 = self.alternative_items.all()
        i4 = self.stocks_items.all()
        i5 = list(i1) + list(i2) + list(i3) + list(i4)
        return i5

    def __get_amount(self) -> float:
        if not hasattr(self, "_amount"):
            items = self.get_items()
            if not items:
                return 0
            self._amount = sum([item.get_bucket_value() for item in items])
        return self._amount

    def get_amount(self) -> str:
        amount = self.__get_amount()
        return "{:,.2f} €".format(amount)

    def __get_total(self) -> float:
        if not hasattr(self, "_total"):
            buckets = list(Bucket.objects.filter(user=self.user))
            self._total = sum([bucket.__get_amount() for bucket in buckets])
        return self._total

    def get_percentage(self) -> str:
        total = self.__get_total()
        amount = self.__get_amount()
        if total == 0:
            return "0.00 %"
        return "{:,.2f} %".format(amount / total * 100)

    def get_diff(self) -> str:
        wanted = self.wanted_percentage * self.__get_total() / 100
        amount = self.__get_amount()
        diff = wanted - amount
        return "{:,.2f} €".format(diff)
