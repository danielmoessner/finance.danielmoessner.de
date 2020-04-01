from django.db.models import Sum, Q
from django.utils import timezone
from django.db import models

from apps.users.models import StandardUser
from apps.core.models import Timespan as CoreTimespan, Account as CoreAccount, Depot as CoreDepot
from apps.crypto.utils import round_sigfigs


class Depot(CoreDepot):
    user = models.ForeignKey(StandardUser, editable=False, related_name="crypto_depots", on_delete=models.CASCADE)
    # query optimization
    value = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)

    # getters
    def get_value(self):
        if self.value is None:
            self.value = 0
            for asset in list(self.assets.all()):
                self.value += asset.get_value()
            self.save()
        return self.value

    def get_stats(self):
        return {
            'Value': self.get_value()
        }

    # setters
    def reset_all(self):
        Depot.objects.filter(pk=self.pk).update(value=None)
        Asset.objects.filter(depot=self).update(value=None, amount=None, price=None)
        Account.objects.filter(depot=self).update(value=None)
        AccountAssetStats.objects.filter(account__in=self.accounts.all()).update(value=None, amount=None)


class Account(CoreAccount):
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name="accounts")
    # query optimization
    value = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)

    # getters
    def get_stats(self):
        return {
            'Value': self.get_value()
        }

    def get_value(self):
        if self.value is None:
            # create all asset stats so that the calculated data is correct
            if self.asset_stats.all().count() != self.depot.assets.all().count():
                for asset in self.depot.assets.all():
                    AccountAssetStats.objects.get_or_create(asset=asset, account=self)
            # sum up the values
            self.value = 0
            for stats in list(self.asset_stats.select_related('asset', 'account')):
                self.value += stats.get_value()
            self.save()
        return self.value

    def get_asset_stats(self, asset):
        stats, created = AccountAssetStats.objects.get_or_create(asset=asset, account=self)
        return stats

    def get_value_asset(self, asset):
        stats = self.get_asset_stats(asset)
        return stats.get_value()

    def get_amount_asset(self, asset):
        stats = self.get_asset_stats(asset)
        return stats.get_amount()


class Asset(models.Model):
    symbol = models.CharField(max_length=5)
    depot = models.ForeignKey(Depot, related_name='assets', on_delete=models.CASCADE)
    # query optimization
    value = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    amount = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    price = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return '{}'.format(self.symbol)

    # getters
    def get_stats(self):
        return {
            'Amount': self.get_amount(),
            'Value': self.get_value()
        }

    def get_price(self):
        if self.price is None:
            price = Price.objects.filter(symbol=self.symbol).order_by('date').last().price or 0
            self.price = price
            self.save()
        return self.price

    def get_value(self):
        if self.value is None:
            amount = self.get_amount()
            price = self.get_price()
            self.value = amount * price
            self.save()
        return self.value

    def get_account_stats(self, account):
        stats, created = AccountAssetStats.objects.get_or_create(asset=self, account=account)
        return stats

    def get_value_account(self, account):
        stats = self.get_account_stats(account)
        return stats.get_value()

    def get_amount_account(self, account):
        stats = self.get_account_stats(account)
        return stats.get_amount()

    def get_amount(self):
        if self.amount is None:
            trade_buy_amount = Trade.objects \
                                   .filter(buy_asset=self, account__in=self.depot.accounts.all()) \
                                   .aggregate(Sum('buy_amount'))['buy_amount__sum'] or 0
            trade_sell_amount = Trade.objects \
                                    .filter(sell_asset=self, account__in=self.depot.accounts.all()) \
                                    .aggregate(Sum('sell_amount'))['sell_amount__sum'] or 0
            transaction_fees_amount = Transaction.objects \
                                          .filter(asset=self, from_account__in=self.depot.accounts.all()) \
                                          .aggregate(Sum('fees'))['fees__sum'] or 0
            flow_amount = Flow.objects \
                .filter(asset=self) \
                .aggregate(Sum('flow'))['flow__sum'] or 0
            self.amount = trade_buy_amount - trade_sell_amount - transaction_fees_amount + flow_amount
            self.save()
        return round_sigfigs(self.amount, 4)


class AccountAssetStats(models.Model):
    account = models.ForeignKey(Account, related_name='asset_stats', on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, related_name='account_stats', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    value = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)

    # getters
    def get_amount(self):
        if self.amount is None:
            trade_buy_amount = Trade.objects \
                                   .filter(buy_asset=self.asset, account=self.account) \
                                   .aggregate(Sum('buy_amount'))['buy_amount__sum'] or 0
            trade_sell_amount = Trade.objects \
                                    .filter(sell_asset=self.asset, account=self.account) \
                                    .aggregate(Sum('sell_amount'))['sell_amount__sum'] or 0
            transaction_to_amount = Transaction.objects \
                                        .filter(asset=self.asset, to_account=self.account) \
                                        .aggregate(Sum('amount'))['amount__sum'] or 0
            transaction_from_and_fees_amount = Transaction.objects \
                .filter(asset=self.asset, from_account=self.account) \
                .aggregate(Sum('fees'), Sum('amount'))
            flow_amount = Flow.objects \
                .filter(asset=self.asset, account=self.account) \
                .aggregate(Sum('flow'))['flow__sum'] or 0
            transaction_from_amount = transaction_from_and_fees_amount['amount__sum'] or 0
            transaction_fees_amount = transaction_from_and_fees_amount['fees__sum'] or 0
            trade_amount = trade_buy_amount - trade_sell_amount
            transaction_amount = transaction_to_amount - transaction_fees_amount - transaction_from_amount
            self.amount = trade_amount + transaction_amount + flow_amount
            self.save()
        return round_sigfigs(self.amount, 4)

    def get_value(self):
        if self.value is None:
            amount = self.get_amount()
            price = self.asset.get_price()
            self.value = amount * price
            self.save()
        return self.value


class Trade(models.Model):
    account = models.ForeignKey(Account, related_name="trades", on_delete=models.PROTECT)
    date = models.DateTimeField()
    buy_amount = models.DecimalField(max_digits=20, decimal_places=8)
    buy_asset = models.ForeignKey(Asset, related_name="buy_trades", on_delete=models.PROTECT)
    sell_amount = models.DecimalField(max_digits=20, decimal_places=8)
    sell_asset = models.ForeignKey(Asset, related_name="sell_trades", on_delete=models.PROTECT)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        account = str(self.account)
        date = str(self.date.date())
        buy_asset = str(self.buy_asset)
        buy_amount = str(self.buy_amount)
        sell_asset = str(self.sell_asset)
        sell_amount = str(self.sell_amount)
        return "{} {} {} {} {} {}".format(date, account, buy_amount, buy_asset, sell_amount, sell_asset)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        self.account.depot.reset_all()

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y %H:%M")


class Transaction(models.Model):
    asset = models.ForeignKey(Asset, related_name="transactions", on_delete=models.PROTECT)
    from_account = models.ForeignKey(Account, related_name="from_transactions", on_delete=models.PROTECT)
    date = models.DateTimeField()
    to_account = models.ForeignKey(Account, related_name="to_transactions", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    fees = models.DecimalField(max_digits=20, decimal_places=8)

    def __str__(self):
        return '{} {} {} {} {}'.format(self.asset, self.date, self.from_account, self.to_account, self.amount)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        self.asset.depot.reset_all()

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y %H:%M")


class Price(models.Model):
    symbol = models.CharField(max_length=5, null=True)
    date = models.DateTimeField()
    price = models.DecimalField(decimal_places=2, max_digits=15, default=0)

    class Meta:
        unique_together = ("symbol", "date")

    def __str__(self):
        return "{} {} {}".format(self.symbol, self.get_date(), self.price)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        [asset.depot.reset_all() for asset in Asset.objects.filter(symbol=self.symbol)]

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y")


class Flow(models.Model):
    account = models.ForeignKey(Account, related_name='flows', on_delete=models.CASCADE)
    date = models.DateTimeField()
    flow = models.DecimalField(max_digits=20, decimal_places=2)
    asset = models.ForeignKey(Asset, related_name='flows', on_delete=models.CASCADE)

    def __str__(self):
        return '{} {} {}'.format(self.get_date(), self.account, self.flow)

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime('%d.%m.%Y %H:%M')


class Timespan(CoreTimespan):
    depot = models.ForeignKey(Depot, editable=False, related_name="timespans", on_delete=models.CASCADE)

    # getters
    def get_start_date(self):
        return timezone.localtime(self.start_date).strftime("%d.%m.%Y %H:%M") if self.start_date else None

    def get_end_date(self):
        return timezone.localtime(self.end_date).strftime("%d.%m.%Y %H:%M") if self.end_date else None
