from django.db import models
from django.db.models import Sum

from apps.users.models import StandardUser
from django.utils import timezone


class Depot(models.Model):
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=False)
    user = models.ForeignKey(StandardUser, on_delete=models.CASCADE, related_name='stock_depots', editable=False)
    # query optimization
    balance = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    value = models.DecimalField(max_digits=20, decimal_places=2, null=True)

    class Meta:
        verbose_name = 'Depot'
        verbose_name_plural = 'Depots'

    def __str__(self):
        return '{}'.format(self.name)

    def reset(self):
        if self.balance is not None or self.value is not None:
            self.balance = None
            self.value = None
            self.save()

    # getters
    def get_stats(self):
        return {
            'Balance': float(self.get_balance()),
            'Value': float(self.get_value())
        }

    def get_value(self):
        if self.value is None:
            self.value = 0
            for stock in self.stocks.all():
                self.value += stock.get_value()
            self.save()
        return self.value

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
            dividends = Dividend.objects.filter(bank__in=banks).aggregate(Sum('dividend'))
            self.balance += dividends['dividend__sum'] if dividends['dividend__sum'] else 0
            self.save()
        return self.balance

    def get_flow_df(self):
        pass

    def get_value_df(self):
        pass


class Bank(models.Model):
    name = models.CharField(max_length=200)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name='banks', editable=False)
    # query optimization
    balance = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    value = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)

    class Meta:
        verbose_name = 'Bank'
        verbose_name_plural = 'Banks'

    def __str__(self):
        return '{}'.format(self.name)

    def reset(self):
        if self.balance is not None or self.value is not None:
            self.balance = None
            self.value = None
            self.save()

    # getters
    def get_stats(self):
        return {
            'Balance': float(self.get_balance()),
            'Value': float(self.get_value())
        }

    def get_value(self):
        if self.value is None:
            self.value = 0
            for stock in self.depot.stocks.all():
                self.value += stock.get_amount_bank(self) * stock.get_price()
                print(self.value, stock)
            self.save()
        return self.value

    def get_balance(self):
        if self.balance is None:
            self.balance = 0
            flows_amount = self.flows.all().aggregate(Sum('flow'))
            self.balance += flows_amount['flow__sum'] if flows_amount['flow__sum'] else 0
            buy_trades_amount = self.trades.filter(buy_or_sell='BUY').aggregate(Sum('money_amount'))
            self.balance -= buy_trades_amount['money_amount__sum'] if buy_trades_amount['money_amount__sum'] else 0
            sell_trades_amount = self.trades.filter(buy_or_sell='SELL').aggregate(Sum('money_amount'))
            self.balance += sell_trades_amount['money_amount__sum'] if sell_trades_amount['money_amount__sum'] else 0
            dividends_amount = self.dividends.all().aggregate(Sum('dividend'))
            self.balance += dividends_amount['dividend__sum'] if dividends_amount['dividend__sum'] else 0
            self.save()
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
        dividends_amount = self.dividends.filter(date__lte=date).aggregate(Sum('dividend'))
        balance += dividends_amount['dividend__sum'] if dividends_amount['dividend__sum'] else 0
        return balance

    def get_flow_df(self):
        pass

    def get_value_df(self):
        pass


class Stock(models.Model):
    name = models.CharField(max_length=50)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name='stocks')
    ticker = models.CharField(max_length=10)
    exchange = models.CharField(max_length=20, default='XETRA')
    # query optimization
    amount = models.PositiveIntegerField(null=True)
    value = models.DecimalField(max_digits=20, decimal_places=2, null=True)

    class Meta:
        verbose_name = 'Stock'
        verbose_name_plural = 'Stocks'

    def __str__(self):
        return '{}'.format(self.name)

    def reset(self):
        if self.amount is not None or self.value is not None:
            self.amount = None
            self.value = None
            self.save()

    # getters
    def get_marketstack_symbol(self):
        return '{}.{}'.format(self.ticker, self.exchange)

    def get_stats(self):
        return {
            'Price': float(self.get_price()),
            'Value': float(self.get_value()),
            'Amount': self.get_amount(),
            'Divdends': float(self.get_dividends())
        }

    def get_dividends(self):
        dividends = self.dividends.all().aggregate(Sum('dividend'))['dividend__sum']
        return dividends if dividends else 0

    def get_amount(self):
        if not self.amount:
            self.amount = 0
            trades = Trade.objects.filter(bank__in=self.depot.banks.all(), stock=self)
            buy_amount = trades.filter(buy_or_sell='BUY').aggregate(Sum('stock_amount'))['stock_amount__sum']
            sell_amount = trades.filter(buy_or_sell='SELL').aggregate(Sum('stock_amount'))['stock_amount__sum']
            self.amount += buy_amount if buy_amount else 0
            self.amount -= sell_amount if sell_amount else 0
            self.save()
        return self.amount

    def get_amount_bank(self, bank):
        amount = 0
        trades = Trade.objects.filter(bank=bank, stock=self)
        buy_amount = trades.filter(buy_or_sell='BUY').aggregate(Sum('stock_amount'))['stock_amount__sum']
        sell_amount = trades.filter(buy_or_sell='SELL').aggregate(Sum('stock_amount'))['stock_amount__sum']
        amount += buy_amount if buy_amount else 0
        amount -= sell_amount if sell_amount else 0
        return amount

    def get_value(self):
        if not self.value:
            self.value = self.get_price() * self.get_amount()
            self.save()
        return self.value

    def get_price(self):
        return Price.objects.filter(ticker=self.ticker, exchange=self.exchange).order_by('date').first().price

    def get_flow_df(self):
        pass

    def get_value_df(self):
        pass


class Flow(models.Model):
    bank = models.ForeignKey(Bank, related_name='flows', on_delete=models.CASCADE)
    date = models.DateTimeField()
    flow = models.DecimalField(max_digits=20, decimal_places=2)
    short_description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Depot'
        verbose_name_plural = 'Depots'

    def __str__(self):
        return '{} - {} - {}'.format(self.get_date(), self.bank, self.flow)

    def save(self, *args, **kwargs):
        if self.pk:
            bank = Flow.objects.get(pk=self.pk).bank
            bank.reset()
            bank.depot.reset()
        super().save(*args, **kwargs)
        self.bank.reset()
        self.bank.depot.reset()

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime('%d.%m.%Y %H:%M')


class Dividend(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='dividends')
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='dividends')
    date = models.DateTimeField()
    dividend = models.DecimalField(decimal_places=2, max_digits=20)

    class Meta:
        verbose_name = 'Dividend'
        verbose_name_plural = 'Dividends'

    def __str__(self):
        return '{} - {} - {}'.format(self.stock, self.get_date(), self.dividend)

    def save(self, *args, **kwargs):
        if self.pk:
            Dividend.objects.get(pk=self.pk).stock.reset()
            Dividend.objects.get(pk=self.pk).bank.reset()
            Dividend.objects.get(pk=self.pk).stock.depot.reset()
        super().save(*args, **kwargs)
        self.stock.reset()
        self.bank.reset()
        self.stock.depot.reset()

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
            trade = Trade.objects.get(pk=self.pk)
            bank = trade.bank
            bank.reset()
            bank.depot.reset()
            stock = trade.stock
            stock.reset()
        super().save(*args, **kwargs)
        self.bank.reset()
        self.bank.depot.reset()
        self.stock.reset()

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime('%d.%m.%Y %H:%M')


class Price(models.Model):
    date = models.DateTimeField()
    ticker = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=20, decimal_places=2)
    exchange = models.CharField(max_length=20)

    def __str__(self):
        return '{} - {} - {}'.format(self.ticker, self.get_date(), self.price)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        affected_stocks = Stock.objects.filter(ticker=self.ticker, exchange=self.exchange).select_related('depot')
        for stock in list(affected_stocks):
            stock.reset()
            stock.depot.reset()
            [bank.reset() for bank in list(stock.depot.banks.all())]

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime('%d.%m.%Y %H:%M')
