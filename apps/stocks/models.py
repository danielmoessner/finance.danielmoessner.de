from datetime import timedelta
from typing import TYPE_CHECKING, Union

from django.db import models
from django.db.models import QuerySet, Sum
from django.utils import timezone

import apps.core.return_calculation as rc
from apps.core import utils
from apps.core.fetchers.base import Fetcher
from apps.core.fetchers.selenium import SeleniumFetcher, SeleniumFetcherInput
from apps.core.fetchers.website import WebsiteFetcher, WebsiteFetcherInput
from apps.core.utils import get_df_from_database
from apps.stocks.fetchers.marketstack import MarketstackFetcher, MarketstackFetcherInput
from apps.users.models import StandardUser


class Depot(models.Model):
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=False)
    user = models.ForeignKey(
        StandardUser,
        on_delete=models.CASCADE,
        related_name="stock_depots",
        editable=False,
    )
    # query optimization
    balance = models.FloatField(null=True)
    value = models.FloatField(null=True)
    invested_capital = models.FloatField(null=True)
    inflow_total = models.FloatField(null=True)
    outflow_total = models.FloatField(null=True)

    if TYPE_CHECKING:
        banks: QuerySet["Bank"]
        stocks: QuerySet["Stock"]

    class Meta:
        verbose_name = "Depot"
        verbose_name_plural = "Depots"
        ordering = ["name"]

    def __str__(self):
        return "{}".format(self.name)

    def reset(self):
        self.balance = None
        self.value = None
        self.invested_capital = None
        self.inflow_total = None
        self.outflow_total = None
        self.recalculate()

    def recalculate(self):
        self.calculate_invested_capital()
        self.calculate_balance()
        self.calculate_value()
        self.calculate_outflow()
        self.calculate_inflow()
        self.save()

    def calculate_invested_capital(self):
        df = rc.get_current_return_df(self.get_flow_df(), self.get_value_df())
        self.invested_capital = rc.get_invested_capital(df)

    def calculate_value(self):
        self.value = 0
        for stock in list(self.stocks.all()):
            if stock.value is None:
                stock.calculate_value()
            value = stock.value
            if value:
                self.value += value

    def calculate_balance(self):
        self.balance = 0
        banks = self.banks.all()
        flows_amount = Flow.objects.filter(bank__in=banks).aggregate(Sum("flow"))
        self.balance += flows_amount["flow__sum"] if flows_amount["flow__sum"] else 0
        buy_trades_amount = Trade.objects.filter(
            bank__in=banks, buy_or_sell="BUY"
        ).aggregate(Sum("money_amount"))
        self.balance -= (
            buy_trades_amount["money_amount__sum"]
            if buy_trades_amount["money_amount__sum"]
            else 0
        )
        sell_trades_amount = Trade.objects.filter(
            bank__in=banks, buy_or_sell="SELL"
        ).aggregate(Sum("money_amount"))
        self.balance += (
            sell_trades_amount["money_amount__sum"]
            if sell_trades_amount["money_amount__sum"]
            else 0
        )
        dividends = Dividend.objects.filter(bank__in=banks).aggregate(Sum("dividend"))
        self.balance += dividends["dividend__sum"] if dividends["dividend__sum"] else 0
        self.balance = float(self.balance)

    def calculate_inflow(self):
        self.inflow_total = self.get_inflow_or_outflow_total("INFLOW")

    def calculate_outflow(self):
        self.outflow_total = self.get_inflow_or_outflow_total("OUTFLOW")

    # getters
    def get_stats(self):
        return {
            "Balance": self.get_balance_display(),
            "Value": self.get_value_display(),
            "Inflow Total": self.get_inflow_display(),
            "Outflow Total": self.get_outflow_display(),
            "Invested Capital*": self.get_invested_capital_display(),
            "info": "*Calculated with the calculated flows and values.",
        }

    def get_value(self) -> float | None:
        return self.value

    def get_balance_display(self):
        if self.balance is None:
            return "404"
        return "{:.2f}".format(self.balance)

    def get_value_display(self):
        if self.value is None:
            return "404"
        return "{:.2f}".format(self.value)

    def get_inflow_display(self):
        if self.inflow_total is None:
            return "404"
        return "{:.2f}".format(self.inflow_total)

    def get_outflow_display(self):
        if self.outflow_total is None:
            return "404"
        return "{:.2f}".format(self.outflow_total)

    def get_invested_capital_display(self):
        if self.invested_capital is None:
            return "404"
        return "{:.2f}".format(self.invested_capital)

    def get_inflow_or_outflow_total(self, inflow_or_outflow):
        flows = Flow.objects.filter(bank__in=self.banks.all())
        if inflow_or_outflow == "INFLOW":
            flows = flows.filter(flow__gt=0)
        elif inflow_or_outflow == "OUTFLOW":
            flows = flows.filter(flow__lt=0)
        else:
            raise Exception("inflow_or_outflow must euqal to INFLOW or OUTFLOW.")
        flow = flows.aggregate(Sum("flow"))["flow__sum"]
        return float(flow) if flow else 0

    def get_df_from_database(self, statement, columns):
        assert str(self.pk) in statement
        return get_df_from_database(statement, columns)

    def get_values(self):
        def get_values_lazy():
            value_df = self.get_value_df()
            if value_df is None:
                return []
            return value_df.reset_index().values.tolist()

        return get_values_lazy

    def get_flows(self):
        def get_flows_lazy():
            return self.get_flow_df().reset_index().values.tolist()

        return get_flows_lazy

    def get_flow_df(self):
        if not hasattr(self, "flow_df"):
            statement = """
                select 
                    date(date) as date,
                    sum(flow) as flow
                from stocks_flow f
                join stocks_bank b on f.bank_id=b.id
                where b.depot_id = {}
                group by date(date)
            """.format(
                self.pk
            )
            # get the flow df
            df = self.get_df_from_database(statement, ["date", "flow"])
            # set the df
            self.flow_df = df
        return self.flow_df

    def get_value_df(self):
        if not hasattr(self, "value_df"):
            self.value_df = utils.sum_up_value_dfs_from_items(self.stocks.all())
        return self.value_df


class Bank(models.Model):
    name = models.CharField(max_length=200)
    depot = models.ForeignKey(
        Depot, on_delete=models.CASCADE, related_name="banks", editable=False
    )
    # query optimization
    balance = models.FloatField(null=True)
    value = models.FloatField(null=True)

    if TYPE_CHECKING:
        stocks: QuerySet["Stock"]
        flows: QuerySet["Flow"]
        trades: QuerySet["Trade"]
        dividends: QuerySet["Dividend"]

    class Meta:
        verbose_name = "Bank"
        verbose_name_plural = "Banks"
        ordering = ["name"]

    def __str__(self):
        return "{}".format(self.name)

    def reset(self):
        self.balance = None
        self.value = None
        self.recalculate()

    def recalculate(self):
        self.calculate_value()
        self.calculate_balance()
        self.save()

    def calculate_value(self):
        self.value = 0
        for stock in self.depot.stocks.all():
            amount = stock.get_amount_bank(self)
            price = stock.get_price()
            self.value += float(amount) * float(price)

    def calculate_balance(self, in_decimal=False):
        self.balance = 0
        flows_amount = self.flows.all().aggregate(Sum("flow"))
        self.balance += flows_amount["flow__sum"] if flows_amount["flow__sum"] else 0
        buy_trades_amount = self.trades.filter(buy_or_sell="BUY").aggregate(
            Sum("money_amount")
        )
        self.balance -= (
            buy_trades_amount["money_amount__sum"]
            if buy_trades_amount["money_amount__sum"]
            else 0
        )
        sell_trades_amount = self.trades.filter(buy_or_sell="SELL").aggregate(
            Sum("money_amount")
        )
        self.balance += (
            sell_trades_amount["money_amount__sum"]
            if sell_trades_amount["money_amount__sum"]
            else 0
        )
        dividends_amount = self.dividends.all().aggregate(Sum("dividend"))
        self.balance += (
            dividends_amount["dividend__sum"]
            if dividends_amount["dividend__sum"]
            else 0
        )
        self.balance = float(self.balance)

    # getters
    def get_stats(self):
        return {"Balance": self.calculate_balance(), "Value": self.get_value_display()}

    def get_value_display(self):
        if self.value is None:
            return "404"
        return "{:.2f}".format(self.value)

    def get_balance_display(self):
        if self.balance is None:
            return "404"
        return "{:.2f}".format(self.balance)

    def get_balance_on_date(
        self, date, exclude_flow=None, exclude_trade=None, exclude_dividend=None
    ):
        # set default values so that we do not get field errors in the queries
        exclude_flow_pk = exclude_flow.pk if exclude_flow else 0
        exclude_trade_pk = exclude_trade.pk if exclude_trade else 0
        exclude_dividend_pk = exclude_dividend.pk if exclude_dividend else 0
        # calculate the balance
        balance = 0
        # flows can have a negative or positive impace
        flows_amount = (
            self.flows.filter(date__lte=date)
            .exclude(pk=exclude_flow_pk)
            .aggregate(Sum("flow"))["flow__sum"]
        )
        balance += flows_amount if flows_amount else 0
        # buy trades have a negative impact regarding the balance
        buy_trades_amount = (
            self.trades.filter(date__lte=date, buy_or_sell="BUY")
            .exclude(pk=exclude_trade_pk)
            .aggregate(Sum("money_amount"))["money_amount__sum"]
        )
        balance -= buy_trades_amount if buy_trades_amount else 0
        # sell trades have a positive impact regarding the balance
        sell_trades_amount = (
            self.trades.filter(date__lte=date, buy_or_sell="SELL")
            .exclude(pk=exclude_trade_pk)
            .aggregate(Sum("money_amount"))["money_amount__sum"]
        )
        balance += sell_trades_amount if sell_trades_amount else 0
        # dividends have a positive impace regarding the balance
        dividends_amount = (
            self.dividends.filter(date__lte=date)
            .exclude(pk=exclude_dividend_pk)
            .aggregate(Sum("dividend"))
        )
        balance += (
            dividends_amount["dividend__sum"]
            if dividends_amount["dividend__sum"]
            else 0
        )
        # return the available balance
        return balance


class Stock(models.Model):
    name = models.CharField(max_length=50)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name="stocks")
    ticker = models.CharField(max_length=10)
    exchange = models.CharField(max_length=20, default="XETRA")
    # query optimization
    top_price = models.ForeignKey(
        "Price", null=True, on_delete=models.SET_NULL, related_name="top_price_stocks"
    )
    price = models.ForeignKey(
        "Price", null=True, on_delete=models.CASCADE, related_name="price_stocks"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    value = models.FloatField(null=True)
    invested_total = models.FloatField(null=True)
    invested_capital = models.FloatField(null=True)
    dividends_amount = models.FloatField(null=True)
    sold_total = models.FloatField(null=True)

    if TYPE_CHECKING:
        trades: QuerySet["Trade"]
        dividends: QuerySet["Dividend"]
        price_fetchers: QuerySet["PriceFetcher"]

    class Meta:
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"
        ordering = ["name"]

    def __str__(self):
        return "{}".format(self.name)

    def reset(self, new_price: Union["Price", None] = None):
        self.amount = None
        self.value = None
        self.invested_capital = None
        self.invested_total = None
        self.dividends_amount = None
        self.sold_total = None
        self.price = None
        self.top_price = None
        self.recalculate_stats(new_price)
        self.save()

    def recalculate_stats(self, new_price: Union["Price", None]):
        self.calculate_top_price()
        self.calculate_price()
        self.calculate_invested_capital()
        self.calculate_dividends_amount()
        self.calculate_sold_total()
        self.calculate_invested_total()
        self.calculate_amount()
        self.calculate_value()

    def calculate_price(self):
        new_price = self.__get_latest_price()
        if new_price is None:
            return
        if self.price is None or new_price.date > self.price.date:
            self.price = new_price

    def calculate_top_price(self):
        date = timezone.now() - timedelta(days=365 * 2)
        top_price = (
            Price.objects.filter(
                ticker=self.ticker, exchange=self.exchange, date__gt=date
            )
            .order_by("-price")
            .first()
        )
        self.top_price = top_price

    def calculate_invested_capital(self):
        df = rc.get_current_return_df(self.get_flow_df(), self.get_value_df())
        self.invested_capital = rc.get_invested_capital(df)

    def calculate_dividends_amount(self):
        dividends = self.dividends.all().aggregate(Sum("dividend"))["dividend__sum"]
        self.dividends_amount = float(dividends) if dividends else 0

    def calculate_sold_total(self):
        sold_total = Trade.objects.filter(buy_or_sell="SELL", stock=self).aggregate(
            Sum("money_amount")
        )["money_amount__sum"]
        self.sold_total = float(sold_total) if sold_total else 0

    def calculate_invested_total(self):
        invested_total = Trade.objects.filter(buy_or_sell="BUY", stock=self).aggregate(
            Sum("money_amount")
        )["money_amount__sum"]
        self.invested_total = float(invested_total) if invested_total else 0

    def calculate_amount(self):
        self.amount = 0
        trades = Trade.objects.filter(bank__in=self.depot.banks.all(), stock=self)
        buy_amount = trades.filter(buy_or_sell="BUY").aggregate(Sum("stock_amount"))[
            "stock_amount__sum"
        ]
        sell_amount = trades.filter(buy_or_sell="SELL").aggregate(Sum("stock_amount"))[
            "stock_amount__sum"
        ]
        self.amount += buy_amount if buy_amount else 0
        self.amount -= sell_amount if sell_amount else 0

    def calculate_value(self):
        if self.price is None or self.amount is None:
            return
        self.value = float(self.price.price) * float(self.amount)

    # getters
    def __get_latest_price(self) -> Union["Price", None]:
        return (
            Price.objects.filter(ticker=self.ticker, exchange=self.exchange)
            .order_by("-date")
            .first()
        )

    def get_marketstack_symbol(self):
        return "{}.{}".format(self.ticker, self.exchange)

    def get_stats(self):
        return {
            "Symbol": f"{self.ticker}.{self.exchange}",
            "Price": self.get_price_display(),
            "Top Price": self.get_top_price_display(),
            "Value": self.get_value_display(),
            "Amount": self.get_amount_display(),
            "Dividends": self.get_dividends_display(),
            "Invested Total": self.get_invested_total_display(),
            "Sold Total": self.get_sold_total_display(),
            "Invested Capital*": self.get_invested_capital_display(),
            "info": "*Calculated with the calculated flows and values.",
        }

    def get_dividends_display(self) -> str:
        if self.dividends_amount is None:
            return "404"
        return "{:.2f}".format(self.dividends_amount)

    def get_invested_capital_display(self) -> str:
        if self.invested_capital is None:
            return "404"
        return "{:.2f}".format(self.invested_capital)

    def get_value_display(self) -> str:
        if self.value is None:
            return "404"
        return "{:.2f}".format(self.value)

    def get_amount_display(self) -> str:
        if self.amount is None:
            return "404"
        return str(self.amount)

    def get_invested_total_display(self) -> str:
        if self.invested_total is None:
            return "404"
        return "{:.2f}".format(self.invested_total)

    def get_sold_total_display(self) -> str:
        if self.sold_total is None:
            return "404"
        return "{:.2f}".format(self.sold_total)

    def get_amount_bank(self, bank):
        amount = 0
        trades = Trade.objects.filter(bank=bank, stock=self)
        buy_amount = trades.filter(buy_or_sell="BUY").aggregate(Sum("stock_amount"))[
            "stock_amount__sum"
        ]
        sell_amount = trades.filter(buy_or_sell="SELL").aggregate(Sum("stock_amount"))[
            "stock_amount__sum"
        ]
        amount += buy_amount if buy_amount else 0
        amount -= sell_amount if sell_amount else 0
        return amount

    def get_values(self):
        def get_values_lazy():
            value_df = self.get_value_df()
            if value_df is None:
                return []
            return value_df.reset_index().values.tolist()

        return get_values_lazy

    def get_flows(self):
        def get_flows_lazy():
            return self.get_flow_df().reset_index().values.tolist()

        return get_flows_lazy

    def get_top_price_display(self) -> str:
        if self.top_price is None or self.price is None:
            return "404"
        return "{:.2f}/{:.2f}".format(
            self.top_price.price, self.top_price.price - self.price.price
        )

    def get_price_display(self) -> str:
        if self.price is None:
            return "404"
        if self.price.is_old:
            return "OLD"
        return "{:.2f}".format(self.price.price)

    def get_price(self) -> float:
        return float(self.price.price) if self.price else 0

    def get_df_from_database(self, statement, columns):
        assert str(self.pk) in statement or (
            self.ticker in statement and self.exchange in statement
        )
        return get_df_from_database(statement, columns)

    def get_flow_df(self):
        # this sql statement generates a flow df for this stock.
        # it selects trades and dividends and unions them
        # thogether. dividends count as negative flows and
        # so do trades that are no buy trades.
        statement = """
            select date(date), sum(dividend + money) as flow
            from (
                select 
                    stock_id,
                    date,
                    case when buy_or_sell = 'BUY' then money_amount 
                    else money_amount * -1 end as money,
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
        """.format(
            self.pk
        )
        # get and return the dataframe
        df = self.get_df_from_database(statement, columns=["date", "flow"])
        return df

    def get_amount_df(self):
        # this statement makes the stock_amount positive or
        # negative depending on what kind of trade it is. afterwards
        # it just cumsum over the amount and returns
        # the actual amount of the stock on one particular date.
        statement = """
            select 
                date,
                sum(amount) over (order by date rows between 
                unbounded preceding and current row) as amount
                from (
                select date(date) as date, sum(amount) as amount
                from (
                    select 
                        date,
                        case when buy_or_sell = 'BUY' then stock_amount 
                        else stock_amount * -1 end as amount
                    from stocks_trade
                    where stock_id = {}
                )
                group by date(date)
            )
        """.format(
            self.pk
        )
        # get and return the df
        df = self.get_df_from_database(statement, columns=["date", "amount"])
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
        """.format(
            self.exchange, self.ticker
        )
        # get and return the df
        df = self.get_df_from_database(statement, ["date", "price"])
        return df

    def get_value_df(self):
        return utils.create_value_df_from_amount_and_price(self)


class PriceFetcher(models.Model):
    stock = models.ForeignKey(
        Stock, on_delete=models.CASCADE, related_name="price_fetchers"
    )
    PRICE_FETCHER_TYPES = (
        ("WEBSITE", "Website"),
        ("SELENIUM", "Selenium"),
        ("MARKETSTACK", "Marketstack"),
    )
    fetcher_type = models.CharField(max_length=250, choices=PRICE_FETCHER_TYPES)
    data = models.JSONField(default=dict)
    error = models.CharField(max_length=1000, blank=True)

    def __str__(self):
        if self.fetcher_type in ["WEBSITE", "SELENIUM"]:
            return "{} - {}".format(self.fetcher_type, self.url)
        return self.fetcher_type

    @property
    def url(self):
        return self.data["website"]

    @property
    def fetcher_class(self) -> type[Fetcher]:
        if self.fetcher_type == "WEBSITE":
            return WebsiteFetcher
        elif self.fetcher_type == "SELENIUM":
            return SeleniumFetcher
        elif self.fetcher_type == "MARKETSTACK":
            return MarketstackFetcher
        raise ValueError("unknown type {}".format(self.fetcher_type))

    @property
    def fetcher_input(
        self,
    ) -> WebsiteFetcherInput | SeleniumFetcherInput | MarketstackFetcherInput:
        if self.fetcher_type == "WEBSITE":
            return WebsiteFetcherInput(**self.data)
        elif self.fetcher_type == "SELENIUM":
            return SeleniumFetcherInput(**self.data)
        elif self.fetcher_type == "MARKETSTACK":
            return MarketstackFetcherInput(**self.data)
        raise ValueError("unknown type {}".format(self.fetcher_type))

    def run(self):
        fetcher: Fetcher = self.fetcher_class()
        success, result = fetcher.fetch_single(self.fetcher_input)
        if success:
            assert isinstance(result, float)
            self.save_price(result)
        else:
            assert isinstance(result, str)
            self.set_error(result)
        return success, result

    def save_price(self, price):
        stock = self.stock
        price = Price(
            **{
                "ticker": stock.ticker,
                "exchange": stock.exchange,
                "date": timezone.now(),
                "price": price,
            }
        )
        price.save()
        self.error = ""
        self.save()

    def set_error(self, error: str):
        self.error = error
        self.save()


class Flow(models.Model):
    bank = models.ForeignKey(Bank, related_name="flows", on_delete=models.CASCADE)
    date = models.DateTimeField()
    flow = models.DecimalField(max_digits=20, decimal_places=2)
    short_description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Depot"
        verbose_name_plural = "Depots"
        ordering = ["-date"]

    def __str__(self):
        return "{} - {} - {}".format(self.get_date(), self.bank, self.flow)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.bank.reset()
        self.bank.depot.reset()

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y %H:%M")


class Dividend(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="dividends")
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name="dividends")
    date = models.DateTimeField()
    dividend = models.DecimalField(decimal_places=2, max_digits=20)

    class Meta:
        verbose_name = "Dividend"
        verbose_name_plural = "Dividends"
        ordering = ["-date"]

    def __str__(self):
        return "{} - {} - {}".format(self.stock, self.get_date(), self.dividend)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.stock.reset()
        self.bank.reset()
        self.stock.depot.reset()

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y %H:%M")


class Trade(models.Model):
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name="trades")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="trades")
    date = models.DateTimeField()
    money_amount = models.DecimalField(max_digits=20, decimal_places=2)
    stock_amount = models.DecimalField(max_digits=10, decimal_places=3)
    TRADE_TYPES = (("BUY", "Buy"), ("SELL", "Sell"))
    buy_or_sell = models.CharField(max_length=50, choices=TRADE_TYPES)

    class Meta:
        verbose_name = "Trade"
        verbose_name_plural = "Trades"
        ordering = ["-date"]

    def __str__(self):
        return "{} - {} - {}".format(self.get_date(), self.bank, self.stock)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.bank.reset()
        self.bank.depot.reset()
        self.stock.reset()

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y %H:%M")


class Price(models.Model):
    date = models.DateTimeField()
    ticker = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=20, decimal_places=2)
    exchange = models.CharField(max_length=20)

    class Meta:
        verbose_name = "Price"
        verbose_name_plural = "Prices"
        ordering = ["-date"]

    def __str__(self):
        return "{} - {} - {}".format(self.ticker, self.get_date(), self.price)

    @property
    def is_old(self) -> bool:
        return self.date < timezone.now() - timedelta(days=1)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        affected_stocks = (
            Stock.objects.filter(ticker=self.ticker, exchange=self.exchange)
            .select_related("depot")
            .prefetch_related("depot__banks")
        )
        for stock in list(affected_stocks):
            stock.reset(self)
            stock.depot.reset()
            [bank.reset() for bank in list(stock.depot.banks.all())]

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y %H:%M")
