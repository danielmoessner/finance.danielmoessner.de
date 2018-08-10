from django.db.models.signals import post_save, post_delete
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils import timezone
from django.db import models

from finance.users.models import StandardUser
from finance.core.models import Timespan as CoreTimespan
from finance.core.models import Account as CoreAccount
from finance.core.models import Depot as CoreDepot

import pandas as pd
import numpy as np
import time


def init_crypto(user):
    pass


class Depot(CoreDepot):
    user = models.ForeignKey(StandardUser, editable=False, related_name="crypto_depots",
                             on_delete=models.CASCADE)

    # getters
    def get_movie(self):
        movie, created = Movie.objects.get_or_create(depot=self, account=None, asset=None)
        return movie


class Account(CoreAccount):
    depot = models.ForeignKey(Depot, on_delete=models.PROTECT, related_name="accounts")

    # getters
    def get_movie(self):
        return self.movies.get(depot=self.depot, asset=None)


class Asset(models.Model):
    private_name = models.CharField(max_length=80, blank=True, null=True)
    private_symbol = models.CharField(max_length=5, blank=True, null=True)
    SYMBOL_CHOICES = (("BTC", "Bitcoin"), ("ETH", "Ethereum"), ("XRP", "Ripple"),
                      ("BCH", "Bitcoin Cash"), ("EOS", "EOS"), ("LTC", "Litecoin"),
                      ("XLM", "Stellar"), ("ADA", "Cardano"), ("TRX", "TRON"), ("MIOTA", "IOTA"),
                      ("USDT", "Tether"), ("NEO", "NEO"), ("DASH", "Dash"),
                      ("BNB", "Binance Coin"), ("XMR", "Monero"), ("ETC", "Ethereum Classic"),
                      ("VEN", "VeChain"), ("XEM", "NEM"), ("OMG", "OmiseGO"), ("ONT", "Ontology"),
                      ("QTUM", "Qtum"), ("ZEC", "Zcash"), ("ICX", "ICON"), ("LSK", "Lisk"),
                      ("DCR", "Decred"), ("ZIL", "Zilliqa"), ("BCN", "Bytecoin"),
                      ("AE", "Aeternity"), ("BTG", "Bitcoin Gold"), ("BTM", "Bytom"),
                      ("SC", "Siacoin"), ("ZRX", "0x"), ("XVG", "Verge"), ("BTS", "BitShares"),
                      ("STEEM", "Steem"), ("NANO", "Nano"), ("REP", "Augur"), ("MKR", "Maker"),
                      ("BCD", "Bitcoin Diamond"), ("DOGE", "Dogecoin"), ("RHOC", "RChain"),
                      ("WAVES", "Waves"), ("WAN", "Wanchain"), ("GNT", "Golem"),
                      ("BTCP", "Bitcoin Private"), ("STRAT", "Stratis"),
                      ("BAT", "Basic Attention Token"), ("PPT", "Populous"), ("DGB", "DigiByte"),
                      ("HT", "Huobi Token"), ("KCS", "KuCoin Shares"), ("SNT", "Status"),
                      ("NAS", "Nebulas"), ("WTC", "Waltonchain"), ("HSR", "Hshare"),
                      ("IOST", "IOST"), ("DGD", "DigixDAO"), ("AION", "Aion"), ("FCT", "Factom"),
                      ("LRC", "Loopring"), ("GXS", "GXChain"), ("CNX", "Cryptonex"),
                      ("KMD", "Komodo"), ("BNT", "Bancor"), ("RDD", "ReddCoin"), ("PAY", "TenX"),
                      ("ARDR", "Ardor"), ("GTC", "Game.com"), ("ARK", "Ark"), ("EUR", "Euro"),
                      ("MONA", "MonaCoin"), ("MAID", "MaidSafeCoin"), ("MOAC", "MOAC"))
    symbol = models.CharField(choices=SYMBOL_CHOICES, max_length=5, null=True, blank=True)
    slug = models.SlugField(unique=True)
    depots = models.ManyToManyField(Depot, related_name="assets")

    def __str__(self):
        asset_symbol = self.symbol if self.symbol else self.private_symbol
        return "{}".format(asset_symbol)

    # getters
    def get_is_private(self):
        return False if self.symbol else True

    def get_movie(self, depot):
        return self.movies.get(depot=depot, account=None)

    def get_acc_movie(self, depot, account):
        return self.movies.get(depot=depot, account=account)

    def get_name(self):
        name = self.get_symbol_display() if self.symbol else self.private_name
        name = "{}".format(name)
        return name

    def get_worth(self, date, amount):
        prices = Price.objects.filter(asset=self)
        dates = [price.date for price in prices]
        closest_date = min(dates, key=lambda d: abs(d - date))
        index = dates.index(closest_date)
        price = prices[index].price
        return float(price * amount)


class Trade(models.Model):
    account = models.ForeignKey(Account, related_name="trades", on_delete=models.CASCADE)
    date = models.DateTimeField()
    buy_amount = models.DecimalField(max_digits=20, decimal_places=8)
    buy_asset = models.ForeignKey(Asset, related_name="buy_trades", on_delete=models.CASCADE)
    sell_amount = models.DecimalField(max_digits=20, decimal_places=8)
    sell_asset = models.ForeignKey(Asset, related_name="sell_trades", on_delete=models.CASCADE)
    fees = models.DecimalField(max_digits=20, decimal_places=8)
    fees_asset = models.ForeignKey(Asset, related_name="trade_fees", on_delete=models.CASCADE)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        account = str(self.account)
        date = str(self.date.date())
        buy_asset = str(self.buy_asset)
        buy_amount = str(self.buy_amount)
        sell_asset = str(self.sell_asset)
        sell_amount = str(self.sell_amount)
        fees = str(self.fees)
        fees_asset = str(self.fees_asset)
        return "{} {} {} {} {} {} {} {}".format(date, account, buy_amount, buy_asset, sell_amount,
                                                sell_asset, fees, fees_asset)

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y %H:%M")


class Transaction(models.Model):
    asset = models.ForeignKey(Asset, related_name="transactions", on_delete=models.CASCADE)
    from_account = models.ForeignKey(Account, related_name="from_transactions",
                                     on_delete=models.CASCADE)
    date = models.DateTimeField()
    to_account = models.ForeignKey(Account, related_name="to_transactions",
                                   on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    fees = models.DecimalField(max_digits=20, decimal_places=8)

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y %H:%M")


class Price(models.Model):
    asset = models.ForeignKey(Asset, related_name="prices", on_delete=models.PROTECT)
    date = models.DateTimeField()
    price = models.DecimalField(decimal_places=2, max_digits=15, default=0)
    currency = models.CharField(max_length=3)

    class Meta:
        unique_together = ("asset", "date", "currency")

    def __str__(self):
        return "{} {} {}".format(self.asset, self.date.strftime("%Y-%m-%d"), self.price)

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y")

    # clean
    @staticmethod
    def clean_db():
        for asset in Asset.objects.all():
            prices = list(Price.objects.filter(asset=asset).order_by("date"))
            prices2 = Price.objects.filter(asset=asset).order_by("date")
            deletes = list()
            for i in range(len(prices)):
                if prices[i].date.replace(hour=0, minute=0, second=0, microsecond=0) in \
                        [price.date.replace(hour=0, minute=0, second=0, microsecond=0)
                         for price in prices2[i+1:]]:
                    deletes.append(i)
            for i in reversed(deletes):
                prices[i].delete()


class Timespan(CoreTimespan):
    depot = models.ForeignKey(Depot, editable=False, related_name="timespans",
                              on_delete=models.CASCADE)

    # getters
    def get_start_date(self):
        return timezone.localtime(self.start_date).strftime("%d.%m.%Y %H:%M") if self.start_date else None

    def get_end_date(self):
        return timezone.localtime(self.end_date).strftime("%d.%m.%Y %H:%M") if self.end_date else None


class Movie(models.Model):
    update_needed = models.BooleanField(default=True)
    depot = models.ForeignKey(Depot, blank=True, null=True, related_name="movies",
                              on_delete=models.CASCADE)
    account = models.ForeignKey(Account, blank=True, null=True, related_name="movies",
                                on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, blank=True, null=True, related_name="movies",
                              on_delete=models.CASCADE)

    class Meta:
        unique_together = ("depot", "account", "asset")

    def __init__(self, *args, **kwargs):
        super(Movie, self).__init__(*args, **kwargs)
        self.data = None
        self.ti = None
        self.timespan_data = None

    def __str__(self):
        text = "{} {} {}".format(self.depot, self.account, self.asset)
        return text.replace("None ", "").replace(" None", "")

    # getters
    def get_df(self, timespan=None):
        if timespan and timespan.start_date and timespan.end_date:
            pictures = self.pictures.filter(d__gte=timespan.start_date,
                                            d__lte=timespan.end_date)
        else:
            pictures = self.pictures
        pictures = pictures.order_by("d")
        pictures = pictures.values("d", "p", "v", "g", "cr", "ttwr", "ca", "cs")
        df = pd.DataFrame(list(pictures), dtype=np.float64)
        if df.empty:
            df = pd.DataFrame(columns=["d", "p", "v", "g", "cr", "ttwr", "ca", "cs"])
        return df

    def get_data(self, timespan=None):
        if timespan and timespan.start_date and timespan.end_date:
            pictures = self.pictures.filter(d__gte=timespan.start_date,
                                            d__lte=timespan.end_date)
        else:
            pictures = Picture.objects.filter(movie=self)
        pictures = pictures.order_by("d")
        data = dict()
        data["d"] = (pictures.values_list("d", flat=True))
        data["p"] = (pictures.values_list("p", flat=True))
        data["v"] = (pictures.values_list("v", flat=True))
        data["g"] = (pictures.values_list("g", flat=True))
        data["cr"] = (pictures.values_list("cr", flat=True))
        data["ttwr"] = (pictures.values_list("ttwr", flat=True))
        data["ca"] = (pictures.values_list("ca", flat=True))
        data["cs"] = (pictures.values_list("cs", flat=True))
        return data

    def get_values(self, user, keys, timespan=None):
        # user in args for query optimization and ease
        data = dict()
        start_picture = None
        end_picture = None
        if timespan and timespan.start_date:
            data["start_date"] = timespan.start_date.strftime(user.date_format)
            try:
                start_picture = self.pictures.filter(d__lt=timespan.start_date).latest("d")
            except ObjectDoesNotExist:
                pass
        if timespan and timespan.end_date:
            data["end_date"] = timespan.end_date.strftime(user.date_format)
            try:
                end_picture = self.pictures.filter(d__lte=timespan.end_date).latest("d")
            except ObjectDoesNotExist:
                pass
        else:
            try:
                end_picture = self.pictures.latest("d")
            except ObjectDoesNotExist:
                pass

        for key in keys:
            if start_picture and end_picture:
                data[key] = getattr(end_picture, key) - getattr(start_picture, key)
            elif end_picture:
                data[key] = getattr(end_picture, key)
            else:
                data[key] = 0
            if user.rounded_numbers:
                data[key] = round(data[key], 2)
                if data[key] == 0.00:
                    data[key] = "x"

        return data

    # update
    @staticmethod
    def init_movies(sender, instance, **kwargs):
        if sender is Account:
            depot = instance.depot
            for asset in depot.assets.exclude(symbol=depot.user.currency):
                Movie.objects.get_or_create(depot=depot, account=instance, asset=asset)
            Movie.objects.get_or_create(depot=depot, account=instance, asset=None)
        elif sender is Asset:
            for depot in instance.depots.all():
                Movie.objects.get_or_create(depot=depot, account=None, asset=instance)
        elif sender is Depot:
            depot = instance
            Movie.objects.get_or_create(depot=depot, account=None, asset=None)

    @staticmethod
    def init_update(sender, instance, **kwargs):
        if sender is Price:
            q1 = Q(asset=instance.asset)
            q2 = Q(asset=None, account=None)
            movies = Movie.objects.filter(q1 | q2)
            movies.update(update_needed=True)
        elif sender is Transaction:
            q1 = Q(account=instance.from_account, asset=instance.asset)
            q2 = Q(account=instance.to_account, asset=instance.asset)
            q3 = Q(depot=instance.from_account.depot, account=None, asset=None)
            movies = Movie.objects.filter(q1 | q2 | q3)
            movies.update(update_needed=True)
        elif sender is Trade:
            q1 = Q(asset=instance.buy_asset, account=instance.account)
            q2 = Q(asset=instance.sell_asset, account=instance.account)
            q3 = Q(depot=instance.account.depot, account=None, asset=None)
            movies = Movie.objects.filter(q1 | q2 | q3)
            movies.update(update_needed=True)

    def update_all(self, force_update=False, disable_update=False):
        if force_update:
            self.depot.movies.update(update_needed=True)

        t1 = time.time()
        for account in self.depot.accounts.all():
            for asset in self.depot.assets.exclude(symbol=self.depot.user.currency):
                movie, created = Movie.objects.get_or_create(depot=self.depot, account=account,
                                                             asset=asset)
                if movie.update_needed and not disable_update:
                    movie.update()
            movie, created = Movie.objects.get_or_create(depot=self.depot, account=account,
                                                         asset=None)
            if movie.update_needed and not disable_update:
                movie.update()
        for asset in self.depot.assets.exclude(symbol=self.depot.user.currency):
            movie, created = Movie.objects.get_or_create(depot=self.depot, account=None,
                                                         asset=asset)
            if movie.update_needed and not disable_update:
                movie.update()
        movie, created = Movie.objects.get_or_create(depot=self.depot, account=None, asset=None)
        if movie.update_needed and not disable_update:
            movie.update()
        t2 = time.time()

        text = "This update took {} minutes.".format(round((t2 - t1) / 60, 2))
        print(text)

    def update(self):
        t1 = time.time()
        if self.account and self.asset:
            df = self.calc_asset_account()
        elif not self.account and self.asset:
            df = self.calc_asset_depot()
        elif self.account and not self.asset:
            df = self.calc_account()
        elif not self.account and not self.asset:
            df = self.calc_depot()
        else:
            raise Exception("Depot, account or asset must be defined in a movie.")

        t2 = time.time()
        old_df = self.get_df()
        old_df.rename(columns={"d": "date", "v": "value", "cs": "current_sum", "g": "gain",
                               "cr": "current_return", "ttwr": "true_time_weighted_return",
                               "p": "price", "ca": "current_amount"}, inplace=True)
        old_df.set_index("date", inplace=True)
        if self.account and self.asset:
            old_df = old_df[["value", "price", "current_amount"]]
        elif not self.account and self.asset:
            old_df = old_df[["value", "current_sum", "gain", "current_return", "price",
                             "current_amount"]]
        elif self.account and not self.asset:
            old_df = old_df[["value"]]
        elif not self.account and not self.asset:
            old_df = old_df[["value", "current_sum", "gain", "current_return",
                             "true_time_weighted_return"]]

        if old_df.equals(df[:len(old_df)]):
            df = df[len(old_df):]
        else:
            self.pictures.all().delete()

        t3 = time.time()
        pictures = list()
        if self.account and self.asset:
            for index, row in df.iterrows():
                picture = Picture(
                    movie=self,
                    d=index,
                    v=row["value"],
                    p=row["price"],
                    ca=row["current_amount"]
                )
                pictures.append(picture)
        elif not self.account and self.asset:
            for index, row in df.iterrows():
                picture = Picture(
                    movie=self,
                    d=index,
                    v=row["value"],
                    cs=row["current_sum"],
                    g=row["gain"],
                    cr=row["current_return"],
                    p=row["price"],
                    ca=row["current_amount"]
                )
                pictures.append(picture)
        elif self.account and not self.asset:
            for index, row in df.iterrows():
                picture = Picture(
                    movie=self,
                    d=index,
                    v=row["value"],
                )
                pictures.append(picture)
        elif not self.account and not self.asset:
            for index, row in df.iterrows():
                picture = Picture(
                    movie=self,
                    d=index, 
                    v=row["value"], 
                    cs=row["current_sum"], 
                    g=row["gain"], 
                    cr=row["current_return"],
                    ttwr=row["true_time_weighted_return"]
                )
                pictures.append(picture)
        Picture.objects.bulk_create(pictures)

        t4 = time.time()
        text = "{} is up to date. --Calc Time: {}% --Other Time: {}%".format(
            self, round((t2 - t1) / (t4 - t1), 2), round((t4 - t2) / (t4 - t1), 2), "%")
        print(text)
        self.update_needed = False
        self.save()

    # calc helpers
    @staticmethod
    def ffadd(df, column):
        column_loc = df.columns.get_loc(column)
        for i in range(1, len(df[column])):
            df.iloc[i, column_loc] = df.iloc[i, column_loc] + df.iloc[i - 1, column_loc]

    @staticmethod
    def ffmultiply(df, column):
        column_loc = df.columns.get_loc(column)
        for i in range(1, len(df[column])):
            df.iloc[i, column_loc] = df.iloc[i, column_loc] * df.iloc[i - 1, column_loc]

    @staticmethod
    def calc_fifo(type_column, ba_column, bs_column, fee_sum_column, ca_column):
        current_sum_row = [0] * len(ba_column)
        for i in range(len(ba_column)):
            current_amount = ca_column.iloc[i]
            if np.around(current_amount, 8) < 0:
                raise Exception("There was more asset sold than available.")
            current_sum = 0
            for k in reversed(range(0, i + 1)):
                if type_column.iloc[k] == "BUY":
                    if k > 0:
                        if np.around(current_amount, 8) > \
                                np.around(ba_column.iloc[k] - ba_column.iloc[k - 1], 8):
                            current_sum += (bs_column.iloc[k] - bs_column.iloc[k - 1]) + \
                                           (fee_sum_column.iloc[k] - fee_sum_column.iloc[k - 1])
                            current_amount -= ba_column.iloc[k] - ba_column.iloc[k - 1]
                        elif np.around(current_amount, 8) <= \
                                np.around(ba_column.iloc[k] - ba_column.iloc[k - 1], 8):
                            current_sum += ((bs_column.iloc[k] - bs_column.iloc[k - 1]) + (
                                    fee_sum_column.iloc[k] - fee_sum_column.iloc[k - 1])) * (
                                    current_amount / (ba_column.iloc[k] - ba_column.iloc[k - 1]))
                            current_amount -= current_amount
                            break
                    else:
                        if np.around(current_amount, 8) <= np.around(ba_column.iloc[k], 8):
                            current_sum += (bs_column.iloc[k] + fee_sum_column.iloc[k]) * \
                                           (current_amount / ba_column.iloc[k])
                            current_amount -= current_amount
                            break
                        else:
                            raise Exception("Something is wrong here.")
            assert np.around(current_amount, 8) == 0  # if fails something wrong in the formula
            current_sum_row[i] = np.around(current_sum, 8)
        return current_sum_row

    # calc
    def calc_asset_depot(self):
        # buy_trades
        buy_trades = Trade.objects.filter(buy_asset=self.asset).select_related("sell_asset",
                                                                               "fees_asset")
        buy_trades_values = buy_trades.values("date", "buy_amount")
        buy_trades_df = pd.DataFrame(list(buy_trades_values), dtype=np.float64)
        buy_trades_df["type"] = "BUY"
        buy_trades_df["buy_sum"] = [trade.sell_asset.get_worth(trade.date, trade.sell_amount) for
                                    trade in buy_trades]
        buy_trades_df["fee_sum_buy"] = [trade.fees_asset.get_worth(trade.date, trade.fees)
                                        for trade in buy_trades]
        if buy_trades_df.empty:
            buy_trades_df = pd.DataFrame(columns=["date", "buy_amount", "type", "buy_sum",
                                                  "fee_sum_buy"])
        buy_trades_df.set_index("date", inplace=True)

        # sell_trades
        sell_trades = Trade.objects.filter(sell_asset=self.asset).select_related("buy_asset")
        sell_trades_values = sell_trades.values("date", "sell_amount", "fees", "fees_asset",
                                                "sell_asset")
        sell_trades_df = pd.DataFrame(list(sell_trades_values), dtype=np.float64)
        if sell_trades_df.empty:
            sell_trades_df = pd.DataFrame(columns=["date", "sell_amount", "fees", "fees_asset",
                                                   "sell_asset", "type", "sell_sum"])
        sell_trades_df.rename(columns={"fees": "fee_amount_sell"}, inplace=True)
        sell_trades_df["type"] = "SELL"
        sell_trades_df["sell_sum"] = [trade.buy_asset.get_worth(trade.date, trade.buy_amount)
                                      for trade in sell_trades]
        sell_trades_df.loc[sell_trades_df.loc[:, "fees_asset"] !=
                           sell_trades_df.loc[:, "sell_asset"], "fee_amount_sell"] = 0
        sell_trades_df.set_index("date", inplace=True)

        # transactions
        transactions = Transaction.objects.filter(asset=self.asset)
        transactions = transactions.values("date", "fees")
        transactions_df = pd.DataFrame(list(transactions), dtype=np.float64)
        transactions_df["type"] = "TRANSACTION"
        if transactions_df.empty:
            transactions_df = pd.DataFrame(columns=["date", "fees", "type"])
        transactions_df.set_index("date", inplace=True)

        # buy_trades, sell_trades and transactions
        tratra_df = pd.concat([buy_trades_df, sell_trades_df, transactions_df], sort=False)
        tratra_df.sort_index(inplace=True)
        tratra_df.fillna(0, inplace=True)
        tratra_df["fee_amount"] = tratra_df["fee_amount_sell"] + tratra_df["fees"]
        Movie.ffadd(tratra_df, "buy_amount")
        Movie.ffadd(tratra_df, "buy_sum")
        Movie.ffadd(tratra_df, "sell_amount")
        Movie.ffadd(tratra_df, "sell_sum")
        Movie.ffadd(tratra_df, "fee_amount")
        Movie.ffadd(tratra_df, "fee_sum_buy")
        tratra_df = tratra_df[tratra_df.type != "TRANSACTION"]
        tratra_df["current_amount"] = tratra_df["buy_amount"] - tratra_df["sell_amount"] - \
            tratra_df["fee_amount"]
        tratra_df["current_sum"] = Movie.calc_fifo(tratra_df["type"], tratra_df["buy_amount"],
                                                   tratra_df["buy_sum"], tratra_df["fee_sum_buy"],
                                                   tratra_df["current_amount"])

        # prices
        prices = Price.objects.filter(asset=self.asset)
        prices = prices.values("date", "price")
        price_df = pd.DataFrame(list(prices), dtype=np.float64)
        if price_df.empty:
            price_df = pd.DataFrame(columns=["date", "price"])
        price_df.set_index("date", inplace=True)

        # all together
        df = pd.concat([price_df, tratra_df], sort=False)
        df.drop(columns=["type", ], inplace=True)
        df.sort_index(inplace=True)
        df.ffill(inplace=True)

        # calc
        df["value"] = df["current_amount"] * df["price"]
        df["gain"] = df["value"] - df["current_sum"]
        df["current_return"] = (df["value"] / df["current_sum"] - 1) * 100

        # return
        df = df[["value", "current_sum", "gain", "current_return", "price", "current_amount"]]
        df.replace([np.nan, np.inf, -np.inf], 0, inplace=True)  # sqlite3 can not save nan or inf
        df[["value", "current_sum", "gain", "current_return", "price"]] = df.drop(
            columns=["current_amount", ]).applymap(lambda x: x.__round__(3))
        df["current_amount"] = df["current_amount"].map(lambda x: x.__round__(8))
        return df

    def calc_asset_account(self):
        # buy_trades
        buy_trades = Trade.objects.filter(buy_asset=self.asset, account=self.account)
        buy_trades_values = buy_trades.values("date", "buy_amount")
        buy_trades_df = pd.DataFrame(list(buy_trades_values), dtype=np.float64)
        if buy_trades_df.empty:
            buy_trades_df = pd.DataFrame(columns=["date", "buy_amount"])
        buy_trades_df.set_index("date", inplace=True)
        
        # sell_trades
        sell_trades = Trade.objects.filter(sell_asset=self.asset, account=self.account)
        sell_trades_values = sell_trades.values("date", "sell_amount", "fees_asset", "sell_asset",
                                                "fees")
        sell_trades_df = pd.DataFrame(list(sell_trades_values), dtype=np.float64)
        if sell_trades_df.empty:
            sell_trades_df = pd.DataFrame(columns=["date", "sell_amount", "fees_asset",
                                                   "sell_asset", "fees"])
        sell_trades_df.rename(columns={"fees": "fee_amount_sell"}, inplace=True)
        sell_trades_df.loc[sell_trades_df.loc[:, "fees_asset"] !=
                           sell_trades_df.loc[:, "sell_asset"], "fee_amount_sell"] = 0
        sell_trades_df.set_index("date", inplace=True)
        
        # to_transactions
        to_transactions = Transaction.objects.filter(asset=self.asset, to_account=self.account)
        to_transactions = to_transactions.values("date", "amount")
        to_transactions_df = pd.DataFrame(list(to_transactions), dtype=np.float64)
        to_transactions_df.rename(columns={"amount": "to_amount"}, inplace=True)
        if to_transactions_df.empty:
            to_transactions_df = pd.DataFrame(columns=["date", "to_amount"])
        to_transactions_df.set_index("date", inplace=True)

        # from_transactions
        from_transactions = Transaction.objects.filter(asset=self.asset, from_account=self.account)
        from_transactions = from_transactions.values("date", "fees", "amount")
        from_transactions_df = pd.DataFrame(list(from_transactions), dtype=np.float64)
        from_transactions_df.rename(columns={"amount": "from_amount"}, inplace=True)
        if from_transactions_df.empty:
            from_transactions_df = pd.DataFrame(columns=["date", "fees", "from_amount"])
        from_transactions_df.set_index("date", inplace=True)
        
        # buy_trades, sell_trades, to_transactions and from_transactions
        tratra_df = pd.concat([buy_trades_df, sell_trades_df, from_transactions_df,
                               to_transactions_df], sort=False)
        tratra_df.sort_index(inplace=True)
        tratra_df.fillna(0, inplace=True)
        tratra_df["fee_amount"] = tratra_df["fee_amount_sell"] + tratra_df["fees"]
        Movie.ffadd(tratra_df, "to_amount")
        Movie.ffadd(tratra_df, "from_amount")
        Movie.ffadd(tratra_df, "buy_amount")
        Movie.ffadd(tratra_df, "sell_amount")
        Movie.ffadd(tratra_df, "fee_amount")
        tratra_df["current_amount"] = \
            tratra_df["buy_amount"] + tratra_df["to_amount"] - \
            tratra_df["sell_amount"] - tratra_df["fee_amount"] - tratra_df["from_amount"]

        # prices
        prices = Price.objects.filter(asset=self.asset)
        prices = prices.values("date", "price")
        price_df = pd.DataFrame(list(prices), dtype=np.float64)
        if price_df.empty:
            price_df = pd.DataFrame(columns=["date", "price"])
        price_df.set_index("date", inplace=True)

        # all together
        df = pd.concat([tratra_df, price_df], sort=False)
        df.sort_index(inplace=True)
        df.ffill(inplace=True)

        # calc
        df["value"] = df["current_amount"] * df["price"]

        # return
        df = df[["value", "price", "current_amount"]]
        df.fillna(0, inplace=True)  # sqlite3 can not save nan or inf
        df[["value", "price"]] = df.drop(columns=["current_amount", ]).applymap(
            lambda x: x.__round__(3))
        df[["current_amount"]] = df[["current_amount"]].applymap(lambda x: x.__round__(8))
        return df

    def calc_account(self):
        df = pd.DataFrame(columns=["value", "date"], dtype=np.float64)

        # assets
        asset_dfs_values = list()
        for asset in self.depot.assets.exclude(symbol="EUR"):
            movie = asset.get_acc_movie(self.depot, self.account)
            asset_df = movie.get_df()
            asset_df = asset_df[["v", "d"]]
            asset_name = asset.get_symbol_display() if asset.symbol else asset.private_name
            asset_df.rename(columns={"v": asset_name + "__value", "d": "date"}, inplace=True)
            asset_dfs_values.append(asset_name + "__value")
            df = pd.concat([df, asset_df], join="outer", ignore_index=True, sort=False)

        # all together
        df["date"] = df["date"].dt.normalize()
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)
        df.ffill(inplace=True)
        df = df[~df.index.duplicated(keep="last")]

        # calc
        df["value"] = df[asset_dfs_values].sum(axis=1, skipna=True)

        # return
        df = df[["value"]]
        df[["value"]] = df[["value"]].applymap(lambda x: x.__round__(3))
        return df

    def calc_depot(self):
        df = pd.DataFrame(columns=["value", "current_sum", "date"], dtype=np.float64)

        # assets
        asset_dfs_values = list()
        asset_dfs_current_sums = list()
        for asset in self.depot.assets.exclude(symbol="EUR"):
            movie = asset.get_movie(self.depot)
            asset_df = movie.get_df()
            asset_df = asset_df[["v", "d", "cs"]]
            asset_name = asset.get_symbol_display() if asset.symbol else asset.private_name
            asset_df.rename(columns={"v": asset_name + "__value", "d": "date",
                                     "cs": asset_name + "__current_sum"}, inplace=True)
            asset_dfs_values.append(asset_name + "__value")
            asset_dfs_current_sums.append(asset_name + "__current_sum")
            df = pd.concat([df, asset_df], join="outer", ignore_index=False, sort=False)

        # all together
        df["date"] = df["date"].dt.normalize()
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)
        df.ffill(inplace=True)
        df = df[~df.index.duplicated(keep="last")]

        # calc
        df["value"] = df[asset_dfs_values].sum(axis=1, skipna=True)
        df["current_sum"] = df[asset_dfs_current_sums].sum(axis=1, skipna=True)
        df["gain"] = df["value"] - df["current_sum"]
        df["current_return"] = ((df["value"] / df["current_sum"]) - 1) * 100
        # ttwr shit
        df["true_time_weighted_return"] = df["value"] / (df["value"].shift(1) + (
                df["current_sum"] - df["current_sum"].shift(1)))
        df["true_time_weighted_return"].replace([np.nan, ], 1, inplace=True)
        Movie.ffmultiply(df, "true_time_weighted_return")
        df["true_time_weighted_return"] = (df["true_time_weighted_return"] - 1) * 100
        # end ttwr shit

        # return
        df = df[["value", "current_sum", "gain", "current_return", "true_time_weighted_return"]]
        df.replace([np.nan, np.inf, -np.inf], 0, inplace=True)  # sqlite3 can not save nan or inf
        df[["value", "current_sum", "gain", "current_return", "true_time_weighted_return"]] = \
            df.applymap(lambda x: x.__round__(3))
        return df


class Picture(models.Model):
    movie = models.ForeignKey(Movie, related_name="pictures", on_delete=models.CASCADE)
    d = models.DateTimeField()

    p = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)
    v = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)
    g = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)
    cr = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)
    ttwr = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)
    ca = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=8)
    cs = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)


post_save.connect(Movie.init_update, sender=Price)
post_delete.connect(Movie.init_update, sender=Price)
post_save.connect(Movie.init_update, sender=Trade)
post_delete.connect(Movie.init_update, sender=Trade)
post_save.connect(Movie.init_update, sender=Transaction)
post_delete.connect(Movie.init_update, sender=Transaction)
post_save.connect(Movie.init_movies, sender=Account)
post_save.connect(Movie.init_movies, sender=Asset)
post_save.connect(Movie.init_movies, sender=Depot)
