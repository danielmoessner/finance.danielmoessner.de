from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Union

import pandas as pd
from django.db import models
from django.db.models import Max, Sum
from django.db.models.query import QuerySet
from django.utils import timezone

import apps.core.return_calculation as rc
from apps.core import utils
from apps.core.fetchers.base import Fetcher
from apps.core.fetchers.selenium import SeleniumFetcher, SeleniumFetcherInput
from apps.core.fetchers.website import WebsiteFetcher, WebsiteFetcherInput
from apps.core.models import Account as CoreAccount
from apps.core.models import Depot as CoreDepot
from apps.core.utils import get_df_from_database
from apps.crypto.fetchers.coingecko import CoinGeckoFetcher, CoinGeckoFetcherInput
from apps.users.models import StandardUser


class Depot(CoreDepot):
    user = models.ForeignKey(
        StandardUser,
        editable=False,
        related_name="crypto_depots",
        on_delete=models.CASCADE,
    )
    # query optimization
    value = models.FloatField(null=True)
    current_return = models.FloatField(null=True)
    invested_capital = models.FloatField(null=True)
    time_weighted_return = models.FloatField(null=True)
    internal_rate_of_return = models.FloatField(null=True)

    if TYPE_CHECKING:
        assets: QuerySet["Asset"]
        accounts: QuerySet["Account"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.assets.filter(symbol="EUR").exists():
            self.assets.create(symbol="EUR")

    # getters
    def __get_flow_df(self):
        statement = """
            select 
                date(date) as date,
                sum(flow) as flow
            from crypto_flow f
            join crypto_account a on f.account_id=a.id
            where a.depot_id = {}
            group by date(date)
        """.format(
            self.pk
        )
        assert str(self.pk) in statement
        return get_df_from_database(statement, ["date", "flow"])

    def get_flow_df(self):
        if not hasattr(self, "flow_df"):
            self.flow_df = self.__get_flow_df()
        return self.flow_df

    def get_value_df(self):
        if not hasattr(self, "value_df"):
            self.value_df = utils.sum_up_value_dfs_from_items(self.assets.all())
        return self.value_df

    def get_value(self):
        return self.value

    def get_value_display(self):
        if self.value is None:
            return "404"
        return "{:,.2f} €".format(self.value)

    def get_current_return_display(self):
        if self.current_return is None:
            return "404"
        return f"{int(self.current_return * 100)} %"

    def get_invested_capital_display(self):
        if self.invested_capital is None:
            return "404"
        return "{:,.2f} €".format(self.invested_capital)

    def get_stats(self):
        return {
            "Value": self.get_value_display(),
            "Invested Capital": self.get_invested_capital_display(),
            "Current Return": self.get_current_return_display(),
        }

    # setters
    def reset(self):
        self.value = None
        self.invested_capital = None
        self.current_return = None
        self.recalculate()

    def recalculate(self):
        self.calculate_value()
        flow_df = self.get_flow_df()
        value_df = self.get_value_df()
        self.calculate_invested_capital(flow_df, value_df)
        self.calculate_current_return(flow_df, value_df)
        self.save()

    def calculate_value(self):
        self.value = 0
        for asset in list(self.assets.all()):
            if asset.value is None:
                continue
            self.value += asset.value

    def calculate_invested_capital(self, flow_df, value_df):
        df = rc.get_current_return_df(flow_df, value_df)
        self.invested_capital = rc.get_invested_capital(df)

    def calculate_current_return(self, flow_df, value_df):
        df = rc.get_current_return_df(flow_df, value_df)
        self.current_return = rc.get_current_return(df)

    def reset_all(self):
        for stats in list(
            AccountAssetStats.objects.filter(account__in=self.accounts.all())
        ):
            stats.reset()
        for asset in list(Asset.objects.filter(depot=self)):
            asset.reset()
        for account in list(Account.objects.filter(depot=self)):
            account.reset()
        self.reset()


class Account(CoreAccount):
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name="accounts")
    # query optimization
    value = models.FloatField(null=True)

    if TYPE_CHECKING:
        asset_stats: QuerySet["AccountAssetStats"]
        trades: QuerySet["Trade"]
        to_transactions: QuerySet["Transaction"]
        from_transactions: QuerySet["Transaction"]

    # getters
    def get_stats(self):
        return {"Value": self.get_value_display()}

    def get_value_display(self):
        if self.value is None:
            return "404"
        return "{:.2f} €".format(self.value)

    def get_asset_stats(self, asset):
        stats, created = AccountAssetStats.objects.get_or_create(
            asset=asset, account=self
        )
        return stats

    def get_amount_asset_before_date(
        self,
        asset,
        date,
        exclude_transactions=None,
        exclude_trades=None,
        exclude_flows=None,
    ):
        stats = self.get_asset_stats(asset)
        return stats.get_amount_before_date(
            date,
            exclude_trades=exclude_trades,
            exclude_flows=exclude_flows,
            exclude_transactions=exclude_transactions,
        )

    # setters
    def reset(self):
        self.value = None
        self.recalculate()

    def recalculate(self):
        self.calculate_value()
        self.save()

    def calculate_value(self):
        self.value = 0
        for stats in list(self.asset_stats.select_related("asset", "account")):
            if self.asset_stats.all().count() != self.depot.assets.all().count():
                for asset in self.depot.assets.all():
                    AccountAssetStats.objects.get_or_create(asset=asset, account=self)
            self.value = 0
            for stats in list(self.asset_stats.select_related("asset", "account")):
                if stats.value is None:
                    continue
                self.value += stats.value


class Asset(models.Model):
    symbol = models.CharField(max_length=5)
    depot = models.ForeignKey(Depot, related_name="assets", on_delete=models.CASCADE)
    # query optimization
    top_price = models.CharField(max_length=100, null=True)
    value = models.FloatField(null=True)
    amount = models.FloatField(null=True)
    price = models.FloatField(null=True)

    if TYPE_CHECKING:
        buy_trades: QuerySet["Trade"]
        sell_trades: QuerySet["Trade"]
        transactions: QuerySet["Transaction"]
        flows: QuerySet["Flow"]
        account_stats: QuerySet["AccountAssetStats"]
        price_fetchers: QuerySet["PriceFetcher"]

    def __str__(self):
        return "{}".format(self.symbol)

    def save(self, *args, **kwargs):
        # uppercase the symbol for convenience
        self.symbol = self.symbol.upper()
        super().save(*args, **kwargs)
        # test that there is a price for the euro asset or
        # the base asset which is euro in this case
        if self.symbol == "EUR" and not Price.objects.filter(symbol="EUR").exists():
            Price.objects.create(symbol="EUR", price=1, date=timezone.now())

    # getters
    def get_df_from_database(self, statement, columns):
        assert str(self.pk) in statement or (self.symbol in statement)
        return utils.get_df_from_database(statement, columns)

    def get_price_df(self):
        # this statement retreives all prices and groups them by date.
        statement = """
            select
                date(date) as date,
                max(price) as price
            from crypto_price
            where symbol='{}'
            group by date(date)
            order by date asc
        """.format(
            self.symbol
        )
        # get and return the df
        df = self.get_df_from_database(statement, ["date", "price"])
        return df

    def get_value_df(self):
        return utils.create_value_df_from_amount_and_price(self)

    def get_amount_df(self):
        # get all possible amount changing objects
        trade_buy_df = pd.DataFrame(
            data=list(
                Trade.objects.filter(buy_asset=self).values("date", "buy_amount")
            ),
            columns=["date", "buy_amount"],
        )
        trade_sell_df = pd.DataFrame(
            data=list(
                Trade.objects.filter(sell_asset=self).values("date", "sell_amount")
            ),
            columns=["date", "sell_amount"],
        )
        transaction_fees_df = pd.DataFrame(
            data=list(Transaction.objects.filter(asset=self).values("date", "fees")),
            columns=["date", "fees"],
        )
        flow_df = pd.DataFrame(
            data=list(Flow.objects.filter(asset=self).values("date", "flow")),
            columns=["date", "flow"],
        )
        # merge everything into a big dataframe
        df = pd.merge(trade_buy_df, trade_sell_df, how="outer", on="date", sort=True)
        df = df.merge(transaction_fees_df, how="outer", on="date", sort=True)
        df = df.merge(flow_df, how="outer", on="date", sort=True)
        # return none if the df is empty
        if df.empty:
            return None
        # set index
        df.set_index("date", inplace=True)
        # replace nan with 0
        df = df.fillna(0)
        # calculate the change on each date
        df.loc[:, "change"] = (
            df.loc[:, "buy_amount"]
            - df.loc[:, "sell_amount"]
            - df.loc[:, "fees"]
            + df.loc[:, "flow"]
        )
        # the amount is the sum of all changes
        df.loc[:, "amount"] = df.loc[:, "change"].cumsum()
        # make the df smaller
        df = df.loc[:, ["amount"]]
        # cast to float otherwise pandas can not reliably use all methods for
        # example interpolate wouldn't work
        df.loc[:, "amount"] = df.loc[:, "amount"].apply(pd.to_numeric, downcast="float")
        # set a standard time for easir calculations and group by date
        df = utils.remove_time_of_date_index_in_df(df)
        df = df.groupby(df.index, sort=True).tail(1)
        # return the df
        return df

    def __get_account_stats(self, account: Account):
        stats, created = AccountAssetStats.objects.get_or_create(
            asset=self, account=account
        )
        return stats

    def get_amount_account(self, account: Account):
        stats = self.__get_account_stats(account)
        return stats.get_amount_display()

    def get_value_account(self, account: Account):
        stats = self.__get_account_stats(account)
        return stats.get_value_display()

    def get_stats(self):
        return {
            "Amount": self.get_amount_display(),
            "Value": self.get_value_display(),
            "Top": self.get_top_price_display(),
        }

    def __get_price(self) -> Union["Price", None]:
        return Price.objects.filter(symbol=self.symbol).order_by("date").last()

    def get_price_display(self) -> str:
        price = self.__get_price()
        if price is None:
            return "404"
        if price.is_old:
            return "OLD"
        return "{:.2f} €".format(price.price)

    def get_top_price_display(self) -> str:
        if self.top_price is None:
            return "404"
        return self.top_price

    def get_value_display(self) -> str:
        if self.value is None:
            return "404"
        return "{:.2f} €".format(self.value)

    def get_amount_display(self) -> str:
        if self.amount is None:
            return "404"
        return "{:.8f}".format(self.amount)

    def get_amount_display_short(self) -> str:
        if self.amount is None:
            return "404"
        return "{:.2f}".format(self.amount)

    # setters
    def reset(self):
        self.value = None
        self.amount = None
        self.price = None
        self.top_price = None
        self.recalculate()

    def recalculate(self):
        self.calculate_amount()
        self.calculate_price()
        self.calculate_value()
        self.calculate_top_price()
        self.save()

    def calculate_value(self):
        amount = self.amount
        price = self.price
        if amount is None or price is None:
            self.value = None
            return
        self.value = float(amount) * float(price)

    def calculate_amount(self):
        trade_buy_amount = (
            Trade.objects.filter(
                buy_asset=self, account__in=self.depot.accounts.all()
            ).aggregate(Sum("buy_amount"))["buy_amount__sum"]
            or 0
        )
        trade_sell_amount = (
            Trade.objects.filter(
                sell_asset=self, account__in=self.depot.accounts.all()
            ).aggregate(Sum("sell_amount"))["sell_amount__sum"]
            or 0
        )
        transaction_fees_amount = (
            Transaction.objects.filter(
                asset=self, from_account__in=self.depot.accounts.all()
            ).aggregate(Sum("fees"))["fees__sum"]
            or 0
        )
        flow_amount = (
            Flow.objects.filter(asset=self).aggregate(Sum("flow"))["flow__sum"] or 0
        )
        self.amount = (
            trade_buy_amount - trade_sell_amount - transaction_fees_amount + flow_amount
        )

    def calculate_price(self):
        price = self.__get_price()
        if price is not None:
            self.price = float(price.price) or 0
        else:
            self.price = 0

    def calculate_top_price(self):
        date = timezone.now() - timedelta(days=365 * 2)
        top_price = Price.objects.filter(symbol=self.symbol, date__gt=date).aggregate(
            Max("price")
        )["price__max"]
        if self.price is None:
            self.top_price = "404"
        elif top_price is None:
            self.top_price = "404"
        else:
            self.top_price = "{:.2f}/{:.2f}".format(
                top_price, float(top_price) - self.price
            )


class AccountAssetStats(models.Model):
    account = models.ForeignKey(
        Account, related_name="asset_stats", on_delete=models.CASCADE
    )
    asset = models.ForeignKey(
        Asset, related_name="account_stats", on_delete=models.CASCADE
    )
    # query optimization
    amount = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    value = models.FloatField(null=True)

    # getters
    def get_amount(self):
        return self.amount

    def get_value(self):
        return self.value

    def get_amount_display(self) -> str:
        if self.amount is None:
            return "404"
        return "{:.8f}".format(self.amount)

    def get_value_display(self) -> str:
        if self.value is None:
            return "404"
        return "{:.2f} €".format(self.value)

    def get_amount_before_date(
        self, date, exclude_transactions=None, exclude_trades=None, exclude_flows=None
    ):
        if exclude_trades is None:
            exclude_trades = []
        if exclude_transactions is None:
            exclude_transactions = []
        if exclude_flows is None:
            exclude_flows = []

        trade_buy_amount = (
            Trade.objects.filter(
                buy_asset=self.asset, account=self.account, date__lt=date
            )
            .exclude(pk__in=exclude_trades)
            .aggregate(Sum("buy_amount"))["buy_amount__sum"]
            or 0
        )
        trade_sell_amount = (
            Trade.objects.filter(
                sell_asset=self.asset, account=self.account, date__lt=date
            )
            .exclude(pk__in=exclude_trades)
            .aggregate(Sum("sell_amount"))["sell_amount__sum"]
            or 0
        )
        transaction_to_amount = (
            Transaction.objects.filter(
                asset=self.asset, to_account=self.account, date__lt=date
            )
            .exclude(pk__in=exclude_transactions)
            .aggregate(Sum("amount"))["amount__sum"]
            or 0
        )
        transaction_from_and_fees_amount = (
            Transaction.objects.filter(
                asset=self.asset, from_account=self.account, date__lt=date
            )
            .exclude(pk__in=exclude_transactions)
            .aggregate(Sum("fees"), Sum("amount"))
        )
        flow_amount = (
            Flow.objects.filter(asset=self.asset, account=self.account, date__lt=date)
            .exclude(pk__in=exclude_flows)
            .aggregate(Sum("flow"))["flow__sum"]
            or 0
        )
        transaction_from_amount = transaction_from_and_fees_amount["amount__sum"] or 0
        transaction_fees_amount = transaction_from_and_fees_amount["fees__sum"] or 0
        trade_amount = trade_buy_amount - trade_sell_amount
        transaction_amount = (
            transaction_to_amount - transaction_fees_amount - transaction_from_amount
        )
        amount = trade_amount + transaction_amount + flow_amount
        return amount

    # setters
    def reset(self):
        self.value = None
        self.amount = None
        self.recalculate()

    def recalculate(self):
        self.calculate_amount()
        self.calculate_value()
        self.save()

    def calculate_value(self):
        if self.amount is None or self.asset.price is None:
            self.value = None
            return
        amount = float(self.amount)
        price = float(self.asset.price)
        self.value = amount * price

    def calculate_amount(self):
        trade_buy_amount = (
            Trade.objects.filter(buy_asset=self.asset, account=self.account).aggregate(
                Sum("buy_amount")
            )["buy_amount__sum"]
            or 0
        )
        trade_sell_amount = (
            Trade.objects.filter(sell_asset=self.asset, account=self.account).aggregate(
                Sum("sell_amount")
            )["sell_amount__sum"]
            or 0
        )
        transaction_to_amount = (
            Transaction.objects.filter(
                asset=self.asset, to_account=self.account
            ).aggregate(Sum("amount"))["amount__sum"]
            or 0
        )
        transaction_from_and_fees_amount = Transaction.objects.filter(
            asset=self.asset, from_account=self.account
        ).aggregate(Sum("fees"), Sum("amount"))
        flow_amount = (
            Flow.objects.filter(asset=self.asset, account=self.account).aggregate(
                Sum("flow")
            )["flow__sum"]
            or 0
        )
        transaction_from_amount = transaction_from_and_fees_amount["amount__sum"] or 0
        transaction_fees_amount = transaction_from_and_fees_amount["fees__sum"] or 0
        trade_amount = trade_buy_amount - trade_sell_amount
        transaction_amount = (
            transaction_to_amount - transaction_fees_amount - transaction_from_amount
        )
        self.amount = trade_amount + transaction_amount + flow_amount


class Trade(models.Model):
    account = models.ForeignKey(
        Account, related_name="trades", on_delete=models.PROTECT
    )
    date = models.DateTimeField()
    buy_amount = models.DecimalField(max_digits=20, decimal_places=8)
    buy_asset = models.ForeignKey(
        Asset, related_name="buy_trades", on_delete=models.PROTECT
    )
    sell_amount = models.DecimalField(max_digits=20, decimal_places=8)
    sell_asset = models.ForeignKey(
        Asset, related_name="sell_trades", on_delete=models.PROTECT
    )

    class Meta:
        ordering = ["-date"]
        unique_together = ("account", "date")

    def __str__(self):
        account = str(self.account)
        buy_asset = str(self.buy_asset)
        buy_amount = str(self.buy_amount)
        sell_asset = str(self.sell_asset)
        sell_amount = str(self.sell_amount)
        return "{} {} {} {} {} {}".format(
            self.get_date(), account, buy_amount, buy_asset, sell_amount, sell_asset
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.reset_deps()

    def delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)
        self.reset_deps()

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y %H:%M")

    # setters
    def reset_deps(self):
        deps: list[Asset | Account | AccountAssetStats | Depot] = []
        deps.append(self.buy_asset)
        deps.append(self.sell_asset)
        for d in self.account.asset_stats.filter(asset=self.buy_asset):
            deps.append(d)
        for d in self.account.asset_stats.filter(asset=self.sell_asset):
            deps.append(d)
        deps.append(self.account)
        deps.append(self.account.depot)
        for dep in deps:
            dep.reset()


class Transaction(models.Model):
    asset = models.ForeignKey(
        Asset, related_name="transactions", on_delete=models.PROTECT
    )
    from_account = models.ForeignKey(
        Account, related_name="from_transactions", on_delete=models.PROTECT
    )
    date = models.DateTimeField()
    to_account = models.ForeignKey(
        Account, related_name="to_transactions", on_delete=models.PROTECT
    )
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    fees = models.DecimalField(max_digits=20, decimal_places=8)

    class Meta:
        unique_together = (("from_account", "date"), ("to_account", "date"))

    def __str__(self):
        return "{} {} {} {} {}".format(
            self.asset, self.date, self.from_account, self.to_account, self.amount
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.reset_deps()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.reset_deps()

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y %H:%M")

    # setters
    def reset_deps(self):
        deps: list[Asset | Account | AccountAssetStats | Depot] = [self.asset]
        for d in self.from_account.asset_stats.filter(asset=self.asset):
            deps.append(d)
        deps.append(self.from_account)
        for d in self.to_account.asset_stats.filter(asset=self.asset):
            deps.append(d)
        deps.append(self.to_account)
        deps.append(self.to_account.depot)
        for dep in deps:
            dep.reset()


class Price(models.Model):
    symbol = models.CharField(max_length=5, null=True)
    date = models.DateTimeField()
    price = models.DecimalField(decimal_places=2, max_digits=15, default=Decimal(0))

    class Meta:
        unique_together = ("symbol", "date")

    def __str__(self):
        return "{} {} {}".format(self.symbol, self.get_date(), self.price)

    @property
    def is_old(self):
        return self.date < timezone.now() - timedelta(days=1)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        [asset.depot.reset_all() for asset in Asset.objects.filter(symbol=self.symbol)]

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        [asset.depot.reset_all() for asset in Asset.objects.filter(symbol=self.symbol)]

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y")

    # setters
    def reset_deps(self):
        affected_assets = (
            Asset.objects.filter(symbol=self.symbol)
            .select_related("depot")
            .prefetch_related("depot__accounts")
        )
        affected_depots: list[Depot] = []
        for asset in affected_assets:
            asset.reset()
            affected_depots.append(asset.depot)
        for depot in affected_depots:
            accounts = list(depot.accounts.all())
            for account in accounts:
                account.reset()
            depot.reset()


class Flow(models.Model):
    account = models.ForeignKey(Account, related_name="flows", on_delete=models.CASCADE)
    date = models.DateTimeField()
    flow = models.DecimalField(max_digits=20, decimal_places=2)
    asset = models.ForeignKey(Asset, related_name="flows", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("account", "date")

    def __str__(self):
        return "{} {} {}".format(self.get_date(), self.account, self.flow)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.reset_deps()

    def delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)
        self.reset_deps()

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y %H:%M")

    # setters
    def reset_deps(self):
        self.asset.reset()
        self.account.reset()
        self.account.depot.reset()


class PriceFetcher(models.Model):
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="price_fetchers"
    )
    PRICE_FETCHER_TYPES = (
        ("WEBSITE", "Website"),
        ("SELENIUM", "Selenium"),
        ("COINGECKO", "CoinGecko"),
    )
    fetcher_type = models.CharField(max_length=250, choices=PRICE_FETCHER_TYPES)
    data = models.JSONField(default=dict)
    error = models.CharField(max_length=1000, blank=True)

    def __str__(self):
        if self.fetcher_type in ["WEBSITE", "SELENIUM"]:
            return "{} - {}".format(self.fetcher_type, self.url)
        return self.fetcher_type

    @property
    def url(self) -> str | None:
        return getattr(self.data, "url", None)

    @property
    def fetcher_class(self) -> type[Fetcher]:
        if self.fetcher_type == "WEBSITE":
            return WebsiteFetcher
        elif self.fetcher_type == "SELENIUM":
            return SeleniumFetcher
        elif self.fetcher_type == "COINGECKO":
            return CoinGeckoFetcher
        raise ValueError("unknown type {}".format(self.fetcher_type))

    @property
    def fetcher_input(
        self,
    ) -> WebsiteFetcherInput | SeleniumFetcherInput | CoinGeckoFetcherInput:
        if self.fetcher_type == "WEBSITE":
            return WebsiteFetcherInput(**self.data)
        elif self.fetcher_type == "SELENIUM":
            return SeleniumFetcherInput(**self.data)
        elif self.fetcher_type == "COINGECKO":
            return CoinGeckoFetcherInput(**self.data)
        raise ValueError("unknown type {}".format(self.fetcher_type))

    def run(self):
        fetcher: Fetcher = self.fetcher_class()
        success, result = fetcher.fetch_single(self.fetcher_input)
        if success:
            self.save_price(result)
        else:
            self.set_error(result)
        return success, result

    def save_price(self, price):
        asset = self.asset
        price = Price(
            **{
                "symbol": asset.symbol,
                "date": timezone.now(),
                "price": price,
            }
        )
        price.save()
        self.error = ""
        self.save()

    def set_error(self, error: str | float):
        assert isinstance(error, str)
        self.error = error
        self.save()
