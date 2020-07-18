from django.db import models
from apps.users.models import StandardUser
from django.utils import timezone


class Depot(models.Model):
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=False)
    user = models.ForeignKey(StandardUser, on_delete=models.CASCADE, related_name='stock_depots', editable=False)

    class Meta:
        verbose_name = 'Depot'
        verbose_name_plural = 'Depots'

    def __str__(self):
        return '{}'.format(self.name)


class Bank(models.Model):
    name = models.CharField(max_length=200)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name='banks', editable=False)

    class Meta:
        verbose_name = 'Bank'
        verbose_name_plural = 'Banks'

    def __str__(self):
        return '{}'.format(self.name)


class Stock(models.Model):
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='stocks')
    date = models.DateTimeField()
    ticker = models.CharField(max_length=10)

    class Meta:
        verbose_name = 'Stock'
        verbose_name_plural = 'Stocks'

    def __str__(self):
        return '{}'.format(self.ticker)


class Flow(models.Model):
    bank = models.ForeignKey(Bank, related_name='flows', on_delete=models.CASCADE)
    date = models.DateTimeField()
    flow = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        verbose_name = 'Depot'
        verbose_name_plural = 'Depots'

    def __str__(self):
        return '{} - {} - {}'.format(self.get_date(), self.bank, self.flow)

    def get_date(self):
        return timezone.localtime(self.date).strftime('%d.%m.%Y %H:%M')


class Trade(models.Model):
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='trades')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='trades')
    date = models.DateTimeField()
    money_amount = models.DecimalField(max_digits=20, decimal_places=2)
    stock_amount = models.PositiveSmallIntegerField()
    TRADE_TYPES = (('BUY', 'Buy'), ('SELL', 'Sell'))
    buy_or_sell = models.CharField(max_length=50, choices=TRADE_TYPES)

    class Meta:
        verbose_name = 'Trade'
        verbose_name_plural = 'Trades'

    def __str__(self):
        return '{} - {} - {}'.format(self.get_date(), self.bank, self.stock)

    def get_date(self):
        return timezone.localtime(self.date).strftime('%d.%m.%Y %H:%M')
