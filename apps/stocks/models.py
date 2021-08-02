import re
import time
from django.conf import settings
from django.db import models
from django.db.models import Sum
from apps.core.utils import get_merged_value_df_from_queryset, sum_up_columns_in_a_dataframe, \
    get_df_from_database
from apps.users.models import StandardUser
from django.utils import timezone
import apps.core.return_calculation as rc
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests


class Depot(models.Model):
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=False)
    user = models.ForeignKey(StandardUser, on_delete=models.CASCADE, related_name='stock_depots', editable=False)
    # query optimization
    balance = models.FloatField(null=True)
    value = models.FloatField(null=True)
    invested_capital = models.FloatField(null=True)
    inflow_total = models.FloatField(null=True)
    outflow_total = models.FloatField(null=True)

    class Meta:
        verbose_name = 'Depot'
        verbose_name_plural = 'Depots'
        ordering = ['name']

    def __str__(self):
        return '{}'.format(self.name)

    def reset(self):
        if self.balance is not None or self.value is not None:
            self.balance = None
            self.value = None
            self.invested_capital = None
            self.inflow_total = None
            self.outflow_total = None
            self.save()

    # getters
    def get_stats(self):
        return {
            'Balance': self.get_balance(),
            'Value': self.get_value(),
            'Inflow Total': self.get_inflow_total(),
            'Outflow Total': self.get_outflow_total(),
            'Invested Capital*': self.get_invested_capital(),
            'info': '*Calculated with the calculated flows and values.'
        }

    def get_inflow_or_outflow_total(self, inflow_or_outflow):
        flows = Flow.objects.filter(bank__in=self.banks.all())
        if inflow_or_outflow == 'INFLOW':
            flows = flows.filter(flow__gt=0)
        elif inflow_or_outflow == 'OUTFLOW':
            flows = flows.filter(flow__lt=0)
        else:
            raise Exception('inflow_or_outflow must euqal to INFLOW or OUTFLOW.')
        flow = flows.aggregate(Sum('flow'))['flow__sum']
        return float(flow) if flow else 0

    def get_inflow_total(self):
        if self.inflow_total is None:
            self.inflow_total = self.get_inflow_or_outflow_total('INFLOW')
            self.save()
        return self.inflow_total

    def get_outflow_total(self):
        if self.outflow_total is None:
            self.outflow_total = self.get_inflow_or_outflow_total('OUTFLOW')
            self.save()
        return self.outflow_total

    def get_invested_capital(self):
        if self.invested_capital is None:
            df = rc.get_current_return_df(self.get_flow_df(), self.get_value_df())
            self.invested_capital = rc.get_invested_capital(df)
            self.save()
        return self.invested_capital

    def get_value(self):
        if self.value is None:
            self.value = 0
            for stock in self.stocks.all():
                value = stock.get_value()
                if value:
                    self.value += value
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
            self.balance = float(self.balance)
            self.save()
        return self.balance

    def get_df_from_database(self, statement, columns):
        assert str(self.pk) in statement
        return get_df_from_database(statement, columns)

    def get_values(self):
        def get_values_lazy():
            return self.get_value_df().reset_index().values.tolist()
        return get_values_lazy

    def get_flows(self):
        def get_flows_lazy():
            return self.get_flow_df().reset_index().values.tolist()
        return get_flows_lazy

    def get_flow_df(self):
        if not hasattr(self, 'flow_df'):
            statement = """
                select 
                    date(date) as date,
                    sum(flow) as flow
                from stocks_flow f
                join stocks_bank b on f.bank_id=b.id
                where b.depot_id = {}
                group by date(date)
            """.format(self.pk)
            # get the flow df
            df = self.get_df_from_database(statement, ['date', 'flow'])
            # set the df
            self.flow_df = df
        return self.flow_df

    def get_value_df(self):
        if not hasattr(self, 'value_df'):
            # get the df with all values
            df = get_merged_value_df_from_queryset(self.stocks.all())
            # fill na values for sum to work correctly
            # note that this is not perfect because i have not tested it
            df = df.fillna(method='ffill').fillna(0)
            # sums up all the values of the assets and interpolates
            df = sum_up_columns_in_a_dataframe(df)
            # remove all the rows where the value is 0 as it doesn't make sense in the calculations
            df = df.loc[df.loc[:, 'value'] != 0]
            # set the df
            self.value_df = df
        return self.value_df


class Bank(models.Model):
    name = models.CharField(max_length=200)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name='banks', editable=False)
    # query optimization
    balance = models.FloatField(null=True)
    value = models.FloatField(null=True)

    class Meta:
        verbose_name = 'Bank'
        verbose_name_plural = 'Banks'
        ordering = ['name']

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
            'Balance': self.get_balance(),
            'Value': self.get_value()
        }

    def get_value(self):
        if self.value is None:
            self.value = 0
            for stock in self.depot.stocks.all():
                self.value += float(stock.get_amount_bank(self)) * float(stock.get_price())
            self.save()
        return self.value

    def get_balance(self, in_decimal=False):
        if self.balance is None or in_decimal is True:
            self.balance = 0
            flows_amount = self.flows.all().aggregate(Sum('flow'))
            self.balance += flows_amount['flow__sum'] if flows_amount['flow__sum'] else 0
            buy_trades_amount = self.trades.filter(buy_or_sell='BUY').aggregate(Sum('money_amount'))
            self.balance -= buy_trades_amount['money_amount__sum'] if buy_trades_amount['money_amount__sum'] else 0
            sell_trades_amount = self.trades.filter(buy_or_sell='SELL').aggregate(Sum('money_amount'))
            self.balance += sell_trades_amount['money_amount__sum'] if sell_trades_amount['money_amount__sum'] else 0
            dividends_amount = self.dividends.all().aggregate(Sum('dividend'))
            self.balance += dividends_amount['dividend__sum'] if dividends_amount['dividend__sum'] else 0
            if not in_decimal:
                self.balance = float(self.balance)
                self.save()
        return self.balance

    def get_balance_on_date(self, date, exclude_flow=None, exclude_trade=None, exclude_dividend=None):
        # set default values so that we do not get field errors in the queries
        exclude_flow_pk = exclude_flow.pk if exclude_flow else 0
        exclude_trade_pk = exclude_trade.pk if exclude_trade else 0
        exclude_dividend_pk = exclude_dividend.pk if exclude_dividend else 0
        # calculate the balance
        balance = 0
        # flows can have a negative or positive impace
        flows_amount = (
            self.flows
                .filter(date__lte=date)
                .exclude(pk=exclude_flow_pk)
                .aggregate(Sum('flow'))['flow__sum']
        )
        balance += flows_amount if flows_amount else 0
        # buy trades have a negative impact regarding the balance
        buy_trades_amount = (
            self.trades
                .filter(date__lte=date, buy_or_sell='BUY')
                .exclude(pk=exclude_trade_pk)
                .aggregate(Sum('money_amount'))['money_amount__sum']
        )
        balance -= buy_trades_amount if buy_trades_amount else 0
        # sell trades have a positive impact regarding the balance
        sell_trades_amount = (
            self.trades
                .filter(date__lte=date, buy_or_sell='SELL')
                .exclude(pk=exclude_trade_pk)
                .aggregate(Sum('money_amount'))['money_amount__sum']
        )
        balance += sell_trades_amount if sell_trades_amount else 0
        # dividends have a positive impace regarding the balance
        dividends_amount = (
            self.dividends
                .filter(date__lte=date)
                .exclude(pk=exclude_dividend_pk)
                .aggregate(Sum('dividend'))
        )
        balance += dividends_amount['dividend__sum'] if dividends_amount['dividend__sum'] else 0
        # return the available balance
        return balance


class Stock(models.Model):
    name = models.CharField(max_length=50)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name='stocks')
    ticker = models.CharField(max_length=10)
    exchange = models.CharField(max_length=20, default='XETRA')
    # query optimization
    amount = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    value = models.FloatField(null=True)
    invested_total = models.FloatField(null=True)
    invested_capital = models.FloatField(null=True)
    dividends_amount = models.FloatField(null=True)
    sold_total = models.FloatField(null=True)
    price = models.FloatField(null=True)

    class Meta:
        verbose_name = 'Stock'
        verbose_name_plural = 'Stocks'
        ordering = ['name']

    def __str__(self):
        return '{}'.format(self.name)

    def reset(self):
        self.amount = None
        self.value = None
        self.invested_capital = None
        self.invested_total = None
        self.dividends_amount = None
        self.sold_total = None
        self.price = None
        self.save()

    # getters
    def get_marketstack_symbol(self):
        return '{}.{}'.format(self.ticker, self.exchange)

    def get_stats(self):
        return {
            'Price': self.get_price(),
            'Value': self.get_value(),
            'Amount': self.get_amount(),
            'Divdends': self.get_dividends(),
            'Invested Total': self.get_invested_total(),
            'Sold Total': self.get_sold_total(),
            'Invested Capital*': self.get_invested_capital(),
            'info': '*Calculated with the calculated flows and values.'
        }

    def get_invested_capital(self):
        if self.invested_capital is None:
            df = rc.get_current_return_df(self.get_flow_df(), self.get_value_df())
            self.invested_capital = rc.get_invested_capital(df)
            self.save()
        return self.invested_capital

    def get_dividends(self):
        if self.dividends_amount is None:
            dividends = self.dividends.all().aggregate(Sum('dividend'))['dividend__sum']
            self.dividends_amount = float(dividends) if dividends else 0
            self.save()
        return self.dividends_amount

    def get_sold_total(self):
        if self.sold_total is None:
            sold_total = (
                Trade.objects.filter(buy_or_sell='SELL', stock=self).aggregate(Sum('money_amount'))['money_amount__sum']
            )
            self.sold_total = float(sold_total) if sold_total else 0
        return self.sold_total

    def get_invested_total(self):
        if self.invested_total is None:
            invested_total = (
                Trade.objects.filter(buy_or_sell='BUY', stock=self).aggregate(Sum('money_amount'))['money_amount__sum']
            )
            self.invested_total = float(invested_total) if invested_total else 0
            self.save()
        return self.invested_total

    def get_amount(self):
        if self.amount is None:
            self.amount = 0
            trades = Trade.objects.filter(bank__in=self.depot.banks.all(), stock=self)
            buy_amount = trades.filter(buy_or_sell='BUY').aggregate(Sum('stock_amount'))['stock_amount__sum']
            sell_amount = trades.filter(buy_or_sell='SELL').aggregate(Sum('stock_amount'))['stock_amount__sum']
            self.amount += buy_amount if buy_amount else 0
            self.amount -= sell_amount if sell_amount else 0
            self.save()
        return self.amount

    def get_value(self):
        if self.value is None and self.get_price() is not None and self.get_amount() is not None:
            self.value = float(self.get_price()) * float(self.get_amount())
            self.save()
        return self.value

    def get_amount_bank(self, bank):
        amount = 0
        trades = Trade.objects.filter(bank=bank, stock=self)
        buy_amount = trades.filter(buy_or_sell='BUY').aggregate(Sum('stock_amount'))['stock_amount__sum']
        sell_amount = trades.filter(buy_or_sell='SELL').aggregate(Sum('stock_amount'))['stock_amount__sum']
        amount += buy_amount if buy_amount else 0
        amount -= sell_amount if sell_amount else 0
        return amount

    def get_values(self):
        def get_values_lazy():
            return self.get_value_df().reset_index().values.tolist()
        return get_values_lazy

    def get_flows(self):
        def get_flows_lazy():
            return self.get_flow_df().reset_index().values.tolist()
        return get_flows_lazy

    def get_price(self):
        if self.price is None:
            # every stock always has a price, because a price is fetched every time a stock is added
            prices = Price.objects.filter(ticker=self.ticker, exchange=self.exchange)
            if prices.exists():
                self.price = prices.order_by('date').last().price
            else:
                self.price = 0
            self.save()
        return self.price

    def get_df_from_database(self, statement, columns):
        assert str(self.pk) in statement or (self.ticker in statement and self.exchange in statement)
        return get_df_from_database(statement, columns)

    def get_flow_df(self):
        # this sql statement generates a flow df for this stock. it selects trades and dividends and unions them
        # thogether. dividends count as negative flows and so do trades that are no buy trades.
        statement = """
            select date(date), sum(dividend + money) as flow
            from (
                select 
                    stock_id,
                    date,
                    case when buy_or_sell = 'BUY' then money_amount else money_amount * -1 end as money,
                    0 as dividend
                from stocks_trade t
                union
                select 
                    stock_id, 
                    date, 
                    0 as money, 
                    dividend * -1 as dividend
                from stocks_dividend s
            )
            where stock_id = {}
            group by date(date)
            order by date
        """.format(self.pk)
        # get and return the dataframe
        df = self.get_df_from_database(statement, columns=['date', 'flow'])
        return df

    def get_amount_df(self):
        # this statement makes the stock_amount positive or negative depending on what kind of trade it is. afterwards
        # it just cumsum over the amount and returns the actual amount of the stock on one particular date.
        statement = """
            select 
                date,
                sum(amount) over (order by date rows between unbounded preceding and current row) as amount
                from (
                select date(date) as date, sum(amount) as amount
                from (
                    select 
                        date,
                        case when buy_or_sell = 'BUY' then stock_amount else stock_amount * -1 end as amount
                    from stocks_trade
                    where stock_id = {}
                )
                group by date(date)
            )
        """.format(self.pk)
        # get and return the df
        df = self.get_df_from_database(statement, columns=['date', 'amount'])
        return df

    def get_price_df(self):
        # this statement retreives all prices and groups them by date.
        statement = """
        select 
            date(date) as date, 
            max(price) as price 
        from stocks_price
        where exchange='{}' and ticker='{}'
        group by date(date)
        """.format(self.exchange, self.ticker)
        # get and return the df
        df = self.get_df_from_database(statement, ['date', 'price'])
        return df

    def get_value_df(self):
        # get price and amount df
        price_df = self.get_price_df()
        amount_df = self.get_amount_df()
        # return none if there is nothing to be calculated
        if price_df is None or amount_df is None or price_df.empty or amount_df.empty:
            return None
        # merge dfs into on df
        df = pd.merge(price_df, amount_df, on='date', how='outer', sort=True)
        # set the date column to a daily frequency
        idx = pd.date_range(start=df.index[0], end=df.index[-1], freq='D')
        df = df.reindex(idx, fill_value=np.nan)
        df.index.rename('date', inplace=True)
        # forward fill the amount
        df.loc[:, 'amount'] = df.loc[:, 'amount'].fillna(method='ffill')
        # interpolate the price
        df.loc[:, 'price'] = df.loc[:, 'price'].interpolate(method='time', limit_direction='both')
        # calculate the value
        df.loc[:, 'value'] = df.loc[:, 'amount'] * df.loc[:, 'price']

        # comment out this stuff because it makes no sense in my mind it seems like it was only here because
        # i thought that the calculations might be faster
        # replace 0 with nan as it makes further manipulations easier
        # df.loc[:, 'value'] = df.loc[:, 'value'].replace(0, np.nan)
        # slice the dataframe only keep the important values
        # df = df.loc[df.loc[:, 'value'].notna()]
        # fill nan with 0 as that is the true value
        # df = df.fillna(0)

        # remove unnecessary columns
        df = df.loc[:, ['value']]
        # return the df
        return df


class PriceFetcher(models.Model):
    stock = models.OneToOneField(Stock, on_delete=models.CASCADE, related_name='price_fetcher')
    website = models.URLField()
    target = models.CharField(max_length=250)

    def __str__(self):
        return '{} - {}'.format(self.stock, self.website)

    # getters
    @staticmethod
    def get_price_static(website, target, sleep=10):
        try:
            r = requests.get(website)
        except requests.exceptions.ConnectionError as err:
            return None
        if not settings.DEBUG:
            time.sleep(sleep)
        text = r.text
        soup = BeautifulSoup(text, features='html.parser')
        selection = soup.select_one(target)
        if selection:
            price = re.search('[0-9]+,[0-9]+', str(selection)).group()
            price = price.replace(',', '.')
            price = float(price)
            return price
        return None

    def get_price(self):
        return PriceFetcher.get_price_static(self.website, self.target)


class Flow(models.Model):
    bank = models.ForeignKey(Bank, related_name='flows', on_delete=models.CASCADE)
    date = models.DateTimeField()
    flow = models.DecimalField(max_digits=20, decimal_places=2)
    short_description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Depot'
        verbose_name_plural = 'Depots'
        ordering = ['-date']

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
        ordering = ['-date']

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
    stock_amount = models.DecimalField(max_digits=10, decimal_places=3)
    TRADE_TYPES = (('BUY', 'Buy'), ('SELL', 'Sell'))
    buy_or_sell = models.CharField(max_length=50, choices=TRADE_TYPES)

    class Meta:
        verbose_name = 'Trade'
        verbose_name_plural = 'Trades'
        ordering = ['-date']

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

    class Meta:
        verbose_name = 'Price'
        verbose_name_plural = 'Prices'
        ordering = ['-date']

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
