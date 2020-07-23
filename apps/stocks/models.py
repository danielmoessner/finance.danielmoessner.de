from django.db import models
from django.db.models import Sum

from apps.users.models import StandardUser
from django.utils import timezone


class Depot(models.Model):
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=False)
    user = models.ForeignKey(StandardUser, on_delete=models.CASCADE, related_name='stock_depots', editable=False)
    # query optimization
    balance = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)

    class Meta:
        verbose_name = 'Depot'
        verbose_name_plural = 'Depots'

    def __str__(self):
        return '{}'.format(self.name)

    def reset(self):
        self.balance = None
        self.save()

    # getters
    def get_stats(self):
        return {
            'Balance': float(self.get_balance()),
            'Value': float(0)  # todo
        }

    def get_balance(self):
        if self.balance is None:
            self.balance = 0
            banks = self.banks.all()
            flows_amount = Flow.objects.filter(bank__in=banks).aggregate(Sum('flow'))
            self.balance += flows_amount['flow__sum'] if flows_amount['flow__sum'] else 0
            buy_trades_amount = Trade.objects.filter(bank__in=banks, buy_or_sell='BUY').aggregate(Sum('money_amount'))
            self.balance -= buy_trades_amount['money_amount__sum'] if buy_trades_amount['money_amount__sum'] else 0
            sell_trades_amount = Trade.objects.filter(bank__in=banks, buy_or_sell='SELL').aggregate(Sum('money_amount'))
            self.balance += sell_trades_amount['money_amount__sum'] if sell_trades_amount['money_amount__sum'] else 0
            # self.save()  todo
        return self.balance


class Bank(models.Model):
    name = models.CharField(max_length=200)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name='banks', editable=False)
    # query optimization
    balance = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)

    class Meta:
        verbose_name = 'Bank'
        verbose_name_plural = 'Banks'

    def __str__(self):
        return '{}'.format(self.name)

    def reset(self):
        self.balance = None
        self.save()
        self.depot.reset()

    # getters
    def get_stats(self):
        return {
            'Balance': self.get_balance(),
            'Value': 0  # todo
        }

    def get_balance(self):
        if self.balance is None:
            self.balance = 0
            flows_amount = self.flows.all().aggregate(Sum('flow'))
            self.balance += flows_amount['flow__sum'] if flows_amount['flow__sum'] else 0
            buy_trades_amount = self.trades.filter(buy_or_sell='BUY').aggregate(Sum('money_amount'))
            self.balance -= buy_trades_amount['money_amount__sum'] if buy_trades_amount['money_amount__sum'] else 0
            sell_trades_amount = self.trades.filter(buy_or_sell='SELL').aggregate(Sum('money_amount'))
            self.balance += sell_trades_amount['money_amount__sum'] if sell_trades_amount['money_amount__sum'] else 0
            # self.save()  todo
        return self.balance

    def get_balance_on_date(self, date):
        balance = 0
        flows_amount = self.flows.filter(date__lte=date).aggregate(Sum('flow'))['flow__sum']
        balance += flows_amount if flows_amount else 0
        buy_trades_amount = (
            self.trades.filter(date__lte=date, buy_or_sell='BUY').aggregate(Sum('money_amount'))['money_amount__sum']
        )
        balance -= buy_trades_amount if buy_trades_amount else 0
        sell_trades_amount = (
            self.trades.filter(date__lte=date, buy_or_sell='SELL').aggregate(Sum('money_amount'))['money_amount__sum']
        )
        balance += sell_trades_amount if sell_trades_amount else 0
        return balance


class Stock(models.Model):
    name = models.CharField(max_length=50)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name='stocks')
    ticker = models.CharField(max_length=10)

    class Meta:
        verbose_name = 'Stock'
        verbose_name_plural = 'Stocks'

    def __str__(self):
        return '{}'.format(self.ticker)

    # getters
    def get_stats(self):
        return {
            'Price': 0,
            'Value': 0,
            'Amount': 0
        }


class Flow(models.Model):
    bank = models.ForeignKey(Bank, related_name='flows', on_delete=models.CASCADE)
    date = models.DateTimeField()
    flow = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        verbose_name = 'Depot'
        verbose_name_plural = 'Depots'

    def __str__(self):
        return '{} - {} - {}'.format(self.get_date(), self.bank, self.flow)

    def save(self, *args, **kwargs):
        if self.pk:
            Flow.objects.get(pk=self.pk).bank.reset()
        super().save(*args, **kwargs)
        self.bank.reset()

    # getters
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

    def save(self, *args, **kwargs):
        if self.pk:
            Trade.objects.get(pk=self.pk).bank.reset()
        super().save(*args, **kwargs)
        self.bank.reset()

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime('%d.%m.%Y %H:%M')
