from django.db.models.signals import post_save, post_delete
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils import timezone
from django.db import models

from apps.users.models import StandardUser
from apps.core.models import Timespan as CoreTimespan
from apps.core.models import Account as CoreAccount
from apps.core.models import Depot as CoreDepot

import pandas as pd
import numpy as np
import time
import pytz


def init_crypto(user):
    from apps.core.utils import create_slug
    from django.utils import timezone
    from datetime import timedelta
    import random
    depot = Depot.objects.create(name="Test Depot", user=user)
    user.set_crypto_depot_active(depot)
    # account
    account1 = Account(depot=depot, name="Wallet 1")
    account1.slug = create_slug(account1)
    account1.save()
    account2 = Account(depot=depot, name="Exchange 1")
    account2.slug = create_slug(account2)
    account2.save()
    # asset
    btc = Asset.objects.get(symbol="BTC")
    btc.depots.add(depot)
    eth = Asset.objects.get(symbol="ETH")
    eth.depots.add(depot)
    ltc = Asset.objects.get(symbol="LTC")
    ltc.depots.add(depot)
    eur = Asset.objects.get(symbol="EUR")
    # trade
    date = timezone.now() - timedelta(days=random.randint(50, 300))
    price = btc.get_worth(date, 1.1)
    Trade.objects.create(account=account2, date=date, buy_amount=1.1, buy_asset=btc, fees=2.80, fees_asset=eur,
                         sell_amount=price, sell_asset=eur)
    date = timezone.now() - timedelta(days=random.randint(50, 300))
    price = eth.get_worth(date, 4.1)
    Trade.objects.create(account=account2, date=date, buy_amount=4.1, buy_asset=eth, fees=1.80, fees_asset=eur,
                         sell_amount=price, sell_asset=eur)
    date = timezone.now() - timedelta(days=random.randint(50, 300))
    price = ltc.get_worth(date, 11.7)
    Trade.objects.create(account=account2, date=date, buy_amount=11.7, buy_asset=ltc, fees=3.20, fees_asset=eur,
                         sell_amount=price, sell_asset=eur)
    # transaction
    date = timezone.now() - timedelta(days=random.randint(1, 40))
    Transaction.objects.create(asset=btc, from_account=account2, to_account=account1, date=date, amount=1.09, fees=0.01)
    date = timezone.now() - timedelta(days=random.randint(1, 40))
    Transaction.objects.create(asset=eth, from_account=account2, to_account=account1, date=date, amount=4.05, fees=0.05)
    # timespan
    Timespan.objects.create(depot=depot, name="Default Timespan", start_date=None, end_date=None, is_active=True)
    # movies
    depot.reset_movies()


class Depot(CoreDepot):
    user = models.ForeignKey(StandardUser, editable=False, related_name="crypto_depots",
                             on_delete=models.CASCADE)

    # getters
    def get_movie(self):
        movie, created = Movie.objects.get_or_create(depot=self, account=None, asset=None)
        return movie

    # movies
    def reset_movies(self, delete=False):
        if delete:
            self.movies.all().delete()

        for account in self.accounts.all():
            for asset in self.assets.all():
                Movie.objects.get_or_create(depot=self, account=account, asset=asset)
            Movie.objects.get_or_create(depot=self, account=account, asset=None)
        for asset in self.assets.all():
            Movie.objects.get_or_create(depot=self, account=None, asset=asset)
        Movie.objects.get_or_create(depot=self, account=None, asset=None)

    def update_movies(self, force_update=False):
        if force_update:
            self.movies.update(update_needed=True)

        accounts = self.accounts.all()

        assets = self.assets.exclude(symbol=self.user.currency)

        for movie in Movie.objects.filter(depot=self, account__in=accounts, asset__in=assets):
            if movie.update_needed:
                movie.update()
        for movie in Movie.objects.filter(depot=self, account__in=accounts, asset=None):
            if movie.update_needed:
                movie.update()
        for movie in Movie.objects.filter(depot=self, account=None, asset__in=assets):
            if movie.update_needed:
                movie.update()
        for movie in Movie.objects.filter(depot=self, account=None, asset=None):
            if movie.update_needed:
                movie.update()


class Account(CoreAccount):
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name="accounts")

    # getters
    def get_movie(self):
        return self.movies.get(depot=self.depot, asset=None)


class Asset(models.Model):
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
        return "{}".format(self.symbol)

    # getters
    def get_movie(self, depot):
        return self.movies.get(depot=depot, account=None)

    def get_acc_movie(self, depot, account):
        return self.movies.get(depot=depot, account=account)

    def get_name(self):
        name = self.get_symbol_display()
        name = "{}".format(name)
        return name

    def get_worth(self, date, amount):
        prices = Price.objects.filter(asset=self)  # maybe improve that by getting values list
        dates = [price.date for price in prices]
        if len(dates) > 0:
            closest_date = min(dates, key=lambda d: abs(d - date))
            index = dates.index(closest_date)
            price = float(prices[index].price)
        else:
            price = 0
        return price * float(amount)


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
        return "{} {} {}".format(self.asset, self.get_date(), self.price)

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
        pictures = pictures.values("d", "p", "v", "g", "cr", "twr", "ca", "cs", "f")
        df = pd.DataFrame(list(pictures), dtype=np.float64)
        if df.empty:
            df = pd.DataFrame(columns=["d", "p", "v", "g", "cr", "twr", "ca", "cs", "f"])
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
        data["twr"] = (pictures.values_list("twr", flat=True))
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
                data[key] = "x"

            if user.rounded_numbers:
                if data[key] == "x" or data[key] is None:
                    pass
                elif key in ["cr", "twr", "ca"]:
                    data[key] = round(data[key], 4)
                else:
                    data[key] = round(data[key], 2)

            if data[key] == "x" or data[key] is None:
                pass
            elif key in ["ca"]:
                pass
            elif key in ["cr", "twr"]:
                data[key] = "{} %".format(round(data[key] * 100, 2))
            else:
                data[key] = "{} {}".format(data[key], user.get_currency_display())

        return data

    # init
    @staticmethod
    def init_movies(sender, instance, **kwargs):
        if sender is Account:
            depot = instance.depot
            for asset in depot.assets.exclude(symbol=depot.user.currency):
                Movie.objects.get_or_create(depot=depot, account=instance, asset=asset)
            Movie.objects.get_or_create(depot=depot, account=instance, asset=None)
        elif sender is Asset:
            for depot in instance.depots.all():
                for account in depot.accounts.all():
                    Movie.objects.get_or_create(depot=depot, account=account, asset=instance)
                Movie.objects.get_or_create(depot=depot, account=None, asset=instance)
        elif sender is Depot:
            depot = instance
            Movie.objects.get_or_create(depot=depot, account=None, asset=None)

    @staticmethod
    def init_update(sender, instance, **kwargs):
        if sender is Price:
            q1 = Q(asset=instance.asset)
            q2 = Q(depot__in=instance.asset.depots.all(), asset=None, account=None)
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

    # update
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

        old_df = self.get_df()
        old_df.set_index("d", inplace=True)

        if self.account and self.asset:
            old_df = old_df.loc[:, ["v", "p", "ca"]]
        elif not self.account and self.asset:
            old_df = old_df.loc[:, ["v", "cs", "g", "cr", "p", "ca"]]
        elif self.account and not self.asset:
            old_df = old_df.loc[:, ["v"]]
        elif not self.account and not self.asset:
            old_df = old_df.loc[:, ["v", "cs", "g", "cr", "twr"]]

        if old_df.equals(df.iloc[:len(old_df)]):
            df = df.iloc[len(old_df):]
        else:
            self.pictures.all().delete()

        pictures = list()
        if self.account and self.asset:
            for index, row in df.iterrows():
                picture = Picture(
                    movie=self,
                    d=index,
                    v=row["v"],
                    p=row["p"],
                    ca=row["ca"]
                )
                pictures.append(picture)
        elif not self.account and self.asset:
            for index, row in df.iterrows():
                picture = Picture(
                    movie=self,
                    d=index,
                    v=row["v"],
                    cs=row["cs"],
                    g=row["g"],
                    cr=row["cr"],
                    p=row["p"],
                    ca=row["ca"],
                    f=row["f"]
                )
                pictures.append(picture)
        elif self.account and not self.asset:
            for index, row in df.iterrows():
                picture = Picture(
                    movie=self,
                    d=index,
                    v=row["v"],
                )
                pictures.append(picture)
        elif not self.account and not self.asset:
            for index, row in df.iterrows():
                picture = Picture(
                    movie=self,
                    d=index,
                    v=row["v"],
                    cs=row["cs"],
                    g=row["g"],
                    cr=row["cr"],
                    twr=row["twr"]
                )
                pictures.append(picture)
        Picture.objects.bulk_create(pictures)

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
        current_sum_row = list()
        for i in range(len(ba_column)):
            current_amount = ca_column.iloc[i]
            assert np.around(current_amount, 8) >= 0  # if fails more asset sold than available
            current_sum = 0
            for k in reversed(range(0, i + 1)):
                if type_column.iloc[k] == "BUY":
                    if np.around(current_amount, 8) > np.around(ba_column.iloc[k], 8):
                        assert k != 0  # if fails something is wrong here
                        current_sum += bs_column.iloc[k] + fee_sum_column.iloc[k]
                        current_amount -= ba_column.iloc[k]
                    elif np.around(current_amount, 8) <= np.around(ba_column.iloc[k], 8):
                        current_sum += (bs_column.iloc[k] + fee_sum_column.iloc[k]) * \
                                       (current_amount / ba_column.iloc[k])
                        current_amount -= current_amount
                        break
            assert np.around(current_amount, 8) == 0  # if fails something wrong in the formula
            current_sum_row.append(np.around(current_sum, 8))
        return current_sum_row

    @staticmethod
    def calc_invested_capital(value, flow):
        """
        The asset has a flow and after that occurs a value is determined. The cs is after the flow occurs.
        """
        assert len(value) == len(flow)
        cs = list()
        cs.append(flow[0])
        for i in range(1, len(value)):
            if flow[i] < 0:
                cs.append(cs[-1] * (1 + flow[i] / value[i - 1]))
            elif flow[i] > 0:
                cs.append(cs[-1] + flow[i])
            else:
                cs.append(cs[-1])
        return cs

    # calc
    def calc_asset_depot(self):
        # buy_trades
        buy_trades = Trade.objects.filter(buy_asset=self.asset, account__in=self.depot.accounts.all()).select_related(
            "sell_asset", "fees_asset")
        buy_trades_values = buy_trades.values("date", "buy_amount")
        b_df = pd.DataFrame(list(buy_trades_values), dtype=np.float64)
        if not b_df.empty:
            b_df.rename(columns={"buy_amount": "ba"}, inplace=True)
            b_df.loc[:, "type"] = "BUY"
            b_df.loc[:, "bs"] = [trade.sell_asset.get_worth(trade.date, trade.sell_amount) for trade in buy_trades]
            b_df.loc[:, "bfs"] = [trade.fees_asset.get_worth(trade.date, trade.fees) for trade in buy_trades]
            b_df = b_df.loc[:, ["date", "type", "ba", "bs", "bfs"]]
        else:
            b_df = pd.DataFrame(columns=["date", "type", "ba", "bs", "bfs"])
        b_df.set_index("date", inplace=True)

        # sell_trades
        sell_trades = Trade.objects.filter(sell_asset=self.asset, account__in=self.depot.accounts.all()).select_related(
            "buy_asset")
        sell_trades_values = sell_trades.values("date", "sell_amount", "fees", "fees_asset", "sell_asset")
        s_df = pd.DataFrame(list(sell_trades_values), dtype=np.float64)
        if not s_df.empty:
            s_df.rename(columns={"fees": "sfa", "sell_amount": "sa"}, inplace=True)
            s_df["type"] = "SELL"
            s_df.loc[:, "ss"] = [trade.buy_asset.get_worth(trade.date, trade.buy_amount) for trade in sell_trades]
            s_df.loc[s_df.loc[:, "fees_asset"] != s_df.loc[:, "sell_asset"], "sfa"] = 0
            s_df = s_df.loc[:, ["date", "type", "sa", "sfa", "ss"]]
        else:
            s_df = pd.DataFrame(columns=["date", "type", "sa", "sfa", "ss"])
        s_df.set_index("date", inplace=True)

        # transactions
        transactions = Transaction.objects.filter(asset=self.asset, from_account__in=self.depot.accounts.all())
        transactions = transactions.values("date", "fees")
        t_df = pd.DataFrame(list(transactions), dtype=np.float64)
        if not t_df.empty:
            t_df.rename(columns={"fees": "tfa"}, inplace=True)
            t_df["type"] = "TRANSACTION"
            t_df = t_df.loc[:, ["date", "type", "tfa"]]
        else:
            t_df = pd.DataFrame(columns=["date", "type", "tfa"])
        t_df.set_index("date", inplace=True)

        # buy_trades, sell_trades, transactions
        bst_df = pd.concat([b_df, s_df, t_df], sort=False)
        if not bst_df.empty:
            bst_df.sort_index(inplace=True)
            bst_df.fillna(0, inplace=True)
            bst_df.loc[:, "cf"] = bst_df.loc[:, "bs"] + bst_df.loc[:, "bfs"] - bst_df.loc[:, "ss"]
            bst_df.loc[:, "ca"] = bst_df.loc[:, "ba"].rolling(window=len(bst_df), min_periods=1).sum() - \
                bst_df.loc[:, "sa"].rolling(window=len(bst_df), min_periods=1).sum() - \
                (bst_df.loc[:, "sfa"] + bst_df.loc[:, "tfa"]).rolling(window=len(bst_df), min_periods=1).sum()
            # this works too, but I decided to use the calc_invested_capital for now
            # bst_df.loc[:, "cs"] = Movie.calc_fifo(bst_df.loc[:, "type"], bst_df.loc[:, "ba"], bst_df.loc[:, "bs"],
            #                                       bst_df.loc[:, "bfs"], bst_df.loc[:, "ca"])
            bst_df.index = bst_df.index.to_series().dt.normalize()
            bst_df = bst_df.groupby(by=bst_df.index, sort=False).agg({"ba": "sum", "bs": "sum", "bfs": "sum",
                                                                      "sa": "sum", "sfa": "sum", "ss": "sum",
                                                                      "tfa": "sum", "cf": "sum", "ca": "last"})
            date_series = pd.date_range(start=bst_df.index[0].date(), end=timezone.now().date())
            bst_df = bst_df.reindex(date_series)
            bst_df.loc[:, ["ca"]] = bst_df.loc[:, ["ca"]].ffill()
            bst_df.fillna(0, inplace=True)
        else:
            bst_df = pd.DataFrame(columns=["date", "ba", "bs", "bfs", "sa", "sfa", "ss", "tfa", "cf", "ca", "cs"])
            bst_df.set_index("date", inplace=True)

        # prices
        prices = Price.objects.filter(asset=self.asset)
        prices = prices.values("date", "price")
        p_df = pd.DataFrame(list(prices), dtype=np.float64)
        if not p_df.empty:
            p_df.rename(columns={"price": "cp"}, inplace=True)
            if p_df.empty:
                p_df = pd.DataFrame(columns=["date", "cp"])
            p_df.set_index("date", inplace=True)
            p_df.sort_index(inplace=True)
            p_df.index = p_df.index.to_series().dt.normalize()
            p_df = p_df.groupby(by=p_df.index, sort=False).last()
            date_series = pd.date_range(start=p_df.index[0].date(), end=timezone.now().date())
            p_df = p_df.reindex(date_series)
            p_df.ffill(inplace=True)
        else:
            p_df = pd.DataFrame(columns=["date", "cp"])
            p_df.set_index("date", inplace=True)

        # buy_trades, sell_trades, transactions, prices
        df = pd.concat([p_df, bst_df], axis=1, sort=True)
        if not df.empty:
            df.fillna(0, inplace=True)
            df["cv"] = df["ca"] * df["cp"]
            df.loc[:, "cs"] = Movie.calc_invested_capital(df.loc[:, "cv"].tolist(), df.loc[:, "cf"].tolist())
            df["cg"] = df["cv"] - df["cs"]
            df["cr"] = df["cv"] / df["cs"] - 1
        else:
            df = pd.DataFrame(columns=["date", "cv", "cs", "cg", "cr", "p", "ca", "cf"])
            df.set_index("date", inplace=True)

        # return
        df.replace([np.nan, np.inf, -np.inf], 0, inplace=True)
        df.rename(columns={"cv": "v", "cg": "g", "cp": "p", "cf": "f"}, inplace=True)
        df = df.loc[:, ["v", "cs", "g", "cr", "p", "ca", "f"]]
        df.loc[:, ["v", "g", "p", "f"]] = df.loc[:, ["v", "g", "p", "f"]].applymap(lambda x: round(x, 2))
        df.loc[:, "cr"] = df.loc[:, "cr"].map(lambda x: round(x, 4))
        df.loc[:, "ca"] = df.loc[:, "ca"].map(lambda x: round(x, 8))
        return df

    def calc_asset_account(self):
        # buy_trades
        buy_trades = Trade.objects.filter(buy_asset=self.asset, account=self.account)
        buy_trades_values = buy_trades.values("date", "buy_amount")
        b_df = pd.DataFrame(list(buy_trades_values), dtype=np.float64)
        if not b_df.empty:
            b_df.rename(columns={"buy_amount": "ba"}, inplace=True)
        else:
            b_df = pd.DataFrame(columns=["date", "ba"])
        b_df.set_index("date", inplace=True)

        # sell_trades
        sell_trades = Trade.objects.filter(sell_asset=self.asset, account=self.account)
        sell_trades_values = sell_trades.values("date", "sell_amount", "fees_asset", "sell_asset", "fees")
        s_df = pd.DataFrame(list(sell_trades_values), dtype=np.float64)
        if not s_df.empty:
            s_df.rename(columns={"fees": "sfa", "sell_amount": "sa"}, inplace=True)
            s_df.loc[s_df.loc[:, "fees_asset"] != s_df.loc[:, "sell_asset"], "sfa"] = 0
            s_df.set_index("date", inplace=True)
            s_df = s_df.loc[:, ["sfa", "sa"]]
        else:
            s_df = pd.DataFrame(columns=["date", "sa", "sfa"])
            s_df.set_index("date", inplace=True)
        
        # to_transactions
        to_transactions = Transaction.objects.filter(asset=self.asset, to_account=self.account)
        to_transactions = to_transactions.values("date", "amount")
        t_df = pd.DataFrame(list(to_transactions), dtype=np.float64)
        if not t_df.empty:
            t_df.rename(columns={"amount": "tta"}, inplace=True)
        else:
            t_df = pd.DataFrame(columns=["date", "tta"])
        t_df.set_index("date", inplace=True)

        # from_transactions
        from_transactions = Transaction.objects.filter(asset=self.asset, from_account=self.account)
        from_transactions = from_transactions.values("date", "fees", "amount")
        from_transactions_df = pd.DataFrame(list(from_transactions), dtype=np.float64)
        if not from_transactions_df.empty:
            from_transactions_df.rename(columns={"amount": "fta", "fees": "ftfa"}, inplace=True)
        else:
            from_transactions_df = pd.DataFrame(columns=["date", "ftfa", "fta"])
        from_transactions_df.set_index("date", inplace=True)
        
        # buy_trades, sell_trades, to_transactions, from_transactions
        bsttft_df = pd.concat([b_df, s_df, from_transactions_df, t_df], sort=False)
        if not bsttft_df.empty:
            bsttft_df.sort_index(inplace=True)
            bsttft_df.fillna(0, inplace=True)
            bsttft_df["ca"] = bsttft_df["ba"].rolling(window=len(bsttft_df), min_periods=1).sum() + \
                bsttft_df["tta"].rolling(window=len(bsttft_df), min_periods=1).sum() - \
                bsttft_df["sa"].rolling(window=len(bsttft_df), min_periods=1).sum() - \
                (bsttft_df["sfa"] + bsttft_df["ftfa"]).rolling(window=len(bsttft_df), min_periods=1).sum() - \
                bsttft_df["fta"].rolling(window=len(bsttft_df), min_periods=1).sum()
            bsttft_df.index = bsttft_df.index.to_series().dt.normalize()
            bsttft_df = bsttft_df.groupby(by=bsttft_df.index, sort=False).agg({"ca": "last"})
            date_series = pd.date_range(start=bsttft_df.index[0].date(), end=timezone.now().date())
            bsttft_df = bsttft_df.reindex(date_series)
            bsttft_df.loc[:, ["ca"]] = bsttft_df.loc[:, ["ca"]].ffill()
            bsttft_df = bsttft_df.loc[:, ["ca"]]
        else:
            bsttft_df = pd.DataFrame(columns=["date", "ca"])
            bsttft_df.set_index("date", inplace=True)

        # prices
        prices = Price.objects.filter(asset=self.asset)
        prices = prices.values("date", "price")
        p_df = pd.DataFrame(list(prices), dtype=np.float64)
        if not p_df.empty:
            p_df.rename(columns={"price": "p"}, inplace=True)
            p_df.set_index("date", inplace=True)
            p_df.sort_index(inplace=True)
            p_df.index = p_df.index.to_series().dt.normalize()
            p_df = p_df.groupby(by=p_df.index, sort=False).last()
            date_series = pd.date_range(start=p_df.index[0].date(), end=timezone.now().date())
            p_df = p_df.reindex(date_series)
            p_df.ffill(inplace=True)
        else:
            p_df = pd.DataFrame(columns=["date", "p"])
            p_df.set_index("date", inplace=True)

        # buy_trades, sell_trades, to_transactions, from_transactions, prices
        df = pd.concat([bsttft_df, p_df], axis=1, sort=True)
        if not df.empty:
            df.ffill(inplace=True)
            df["v"] = df["ca"] * df["p"]
        else:
            df = pd.DataFrame(columns=["v", "p", "ca", "date"])
            df.set_index("date", inplace=True)

        # return
        df.replace([np.nan, np.inf, -np.inf], 0, inplace=True)
        df = df.loc[:, ["v", "p", "ca"]]
        df.loc[:, ["v", "p"]] = df.loc[:, ["v", "p"]].applymap(lambda x: round(x, 2))
        df.loc[:, "ca"] = df.loc[:, "ca"].map(lambda x: round(x, 8))
        return df

    def calc_account(self):
        df = pd.DataFrame(columns=["v", "date"], dtype=np.float64)
        df.set_index("date", inplace=True)

        # assets
        assets = list()
        for asset in self.depot.assets.exclude(symbol="EUR"):
            movie = asset.get_acc_movie(self.depot, self.account)
            asset_df = movie.get_df()
            asset_df.set_index("d", inplace=True)
            asset_df = asset_df.loc[:, ["v"]]
            asset_df.rename(columns={"d": "date", "v": asset.symbol + "__v"}, inplace=True)
            assets.append(asset.symbol)
            df = pd.concat([df, asset_df], axis=1, sort=True)

        # all together
        if not df.empty:
            df.fillna(0, inplace=True)
            df["v"] = df.loc[:, [symbol + "__v" for symbol in assets]].sum(axis=1, skipna=True)
        else:
            df = pd.DataFrame(columns=["date", "v"])
            df.set_index("date", inplace=True)

        # return
        df = df.loc[:, ["v"]]
        df.loc[:, "v"] = df.loc[:, "v"].map(lambda x: round(x, 2))
        return df

    def calc_depot(self):
        df = pd.DataFrame(columns=["v", "cs", "date"], dtype=np.float64)
        df.set_index("date", inplace=True)

        # assets
        assets = list()
        for asset in self.depot.assets.exclude(symbol="EUR"):
            movie = asset.get_movie(self.depot)
            asset_df = movie.get_df()
            asset_df.set_index("d", inplace=True)
            asset_df = asset_df.loc[:, ["v", "cs", "f"]]
            asset_df.rename(columns={"v": asset.symbol + "__v", "cs": asset.symbol + "__cs", "f": asset.symbol + "__f"},
                            inplace=True)
            assets.append(asset.symbol)
            df = pd.concat([df, asset_df], axis=1, sort=True)

        # all together
        if not df.empty:
            df.fillna(0, inplace=True)
            df.loc[:, "v"] = df.loc[:, [symbol + "__v" for symbol in assets]].sum(axis=1, skipna=True)
            df.loc[:, "cs"] = df.loc[:, [symbol + "__cs" for symbol in assets]].sum(axis=1, skipna=True)
            df.loc[:, "f"] = df.loc[:, [symbol + "__f" for symbol in assets]].sum(axis=1, skipna=True)
            df = df.loc[:, ["v", "cs", "f"]]
            df.loc[:, "g"] = df.loc[:, "v"] - df.loc[:, "cs"]
            df.loc[:, "cr"] = df.loc[:, "v"] / df.loc[:, "cs"] - 1
            df.loc[:, "twr"] = (df.loc[:, "v"] - df.loc[:, "f"]) / df.loc[:, "v"].shift(1)
            df.loc[np.isinf(df.loc[:, "twr"]), "twr"] = (df["v"] / df.loc[:, "f"]).loc[np.isinf(df.loc[:, "twr"])]
            df.loc[:, "twr"] = df.loc[:, "twr"].fillna(1)
            df.loc[:, "twr"] = df.loc[:, "twr"].cumprod()
            df.loc[:, "twr"] = df.loc[:, "twr"] - 1
        else:
            df = pd.DataFrame(columns=["v", "cs", "g", "twr", "cr", "date"])
            df.set_index("date", inplace=True)

        # return
        df.replace([np.nan, np.inf, -np.inf], 0, inplace=True)  # sqlite3 can not save nan or inf
        df = df.loc[:, ["v", "cs", "g", "twr", "cr"]]
        df.loc[:, ["v", "g", "cs"]] = df.loc[:, ["v", "g", "cs"]].applymap(lambda x: round(x, 2))
        df.loc[:, ["cr", "twr"]] = df.loc[:, ["cr", "twr"]].applymap(lambda x: round(x, 4))
        return df


class Picture(models.Model):
    movie = models.ForeignKey(Movie, related_name="pictures", on_delete=models.CASCADE)
    d = models.DateField()

    p = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=2)
    v = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=2)
    g = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=2)
    f = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=2)
    cs = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=2)
    cr = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=4)
    twr = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=4)
    ca = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=8)


post_save.connect(Movie.init_update, sender=Price)
post_delete.connect(Movie.init_update, sender=Price)
post_save.connect(Movie.init_update, sender=Trade)
post_delete.connect(Movie.init_update, sender=Trade)
post_save.connect(Movie.init_update, sender=Transaction)
post_delete.connect(Movie.init_update, sender=Transaction)
post_save.connect(Movie.init_movies, sender=Account)
post_save.connect(Movie.init_movies, sender=Asset)
post_save.connect(Movie.init_movies, sender=Depot)
