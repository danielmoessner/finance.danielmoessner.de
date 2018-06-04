from django.db.models import Q
from django.conf import settings
from django.db import models

from finance.users.models import StandardUser
from finance.core.models import Timespan as CoreTimespan
from finance.core.models import Account as CoreAccount
from finance.core.models import Depot as CoreDepot
from finance.core.utils import create_slug

from datetime import timedelta, datetime
from decimal import Decimal
import urllib.request
import urllib.error
import pandas
import numpy
import pytz
import time
import json
import os


def init_crypto(user):
    pass


class Depot(CoreDepot):
    user = models.ForeignKey(StandardUser, editable=False, related_name="crypto_depots",
                             on_delete=models.CASCADE)

    def __init__(self, *args, **kwargs):
        super(Depot, self).__init__(*args, **kwargs)
        self.m = None

    # getters
    def get_movie(self):
        if not self.m:
            self.m = self.movies.get(account=None, asset=None, depot=self)
        return self.m

    # update
    def update_prices(self):
        file_path = os.path.join(settings.MEDIA_ROOT, "crypto/prices")
        file_name = time.strftime("%d%m%Y") + ".json"
        file = os.path.join(file_path, file_name)
        if not os.path.exists(file):
            try:
                with urllib.request.urlopen("https://api.coinmarketcap.com/v1/ticker/?convert=" +
                                            self.user.get_currency_display()) as url:
                    data = json.loads(url.read().decode())
                    file_path = os.path.join(settings.MEDIA_ROOT, "crypto/prices")
                    file_name = time.strftime("%d%m%Y") + ".json"
                    file = os.path.join(file_path, file_name)
                    with open(file, "w+") as file:
                        json.dump(data, file)
            except urllib.error.HTTPError:
                return  # error correction
        for asset in Asset.objects.all():
            asset.update_price()


class Account(CoreAccount):
    depot = models.ForeignKey(Depot, on_delete=models.PROTECT, related_name="accounts")

    def __init__(self, *args, **kwargs):
        super(Account, self).__init__(*args, **kwargs)
        self.m = None

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super(Account, self).save(force_insert, force_update, using, update_fields)
        Movie.update_all(self.depot, disable_update=True)

    # getters
    def get_movie(self):
        if not self.m:
            self.m = Movie.objects.get(depot=self.depot, asset=None, account=self)
        return self.m


class Asset(models.Model):
    name = models.CharField(max_length=300)
    symbol = models.CharField(max_length=5, unique=True)
    slug = models.SlugField(unique=True)

    def __init__(self, *args, **kwargs):
        super(Asset, self).__init__(*args, **kwargs)
        self.m = None  # m = movie
        self.acc_m = None  # acc_m = account movie
        self.dep_m = None  # dep_m = depot movie

    def __str__(self):
        return str(self.symbol)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.slug:
            self.slug = create_slug(self)
        super(Asset, self).save(force_insert, force_update, using, update_fields)

    # getters
    def get_movie(self, depot):
        if not self.m:
            self.m = Movie.objects.get(depot=depot, account=None, asset=self)
        return self.m

    def get_acc_movie(self, account):
        if not self.acc_m:
            self.acc_m = Movie.objects.get(depot=account.depot, account=account, asset=self)
        return self.acc_m

    def get_dep_movie(self, depot):
        if not self.dep_m:
            self.dep_m = Movie.objects.get(depot=depot, account=None, asset=self)
        return self.dep_m

    def get_worth(self, date, amount):
        prices = Price.objects.filter(asset=self)
        dates = [price.date for price in prices]
        closest_date = min(dates, key=lambda d: abs(d - date))
        index = dates.index(closest_date)
        price = prices[index].price
        return price * amount

    # move asset from one account to another
    def move(self, date, from_account, amount, to_account, tx_fees):
        ft_account = from_account
        ft_date = date
        ft_buy_amount = self.get_worth(date, amount)
        ft_buy_asset = Asset.objects.get(symbol=from_account.depot.user.get_currency_display())
        ft_sell_amount = amount + tx_fees
        ft_sell_asset = self
        ft_fees = 0
        ft_fees_asset = Asset.objects.get(symbol=from_account.depot.user.get_currency_display())
        from_trade = Trade(account=ft_account, date=ft_date, buy_amount=ft_buy_amount,
                           buy_asset=ft_buy_asset, sell_amount=ft_sell_amount,
                           sell_asset=ft_sell_asset, fees=ft_fees, fees_asset=ft_fees_asset,
                           is_move_trade=True)
        from_trade.save()
        tt_account = to_account
        tt_date = date + timedelta(0, 10)
        tt_buy_amount = amount
        tt_buy_asset = self
        tt_sell_amount = ft_buy_amount
        tt_sell_asset = Asset.objects.get(symbol=from_account.depot.user.get_currency_display())
        tt_fees = tx_fees
        tt_fees_asset = self
        to_trade = Trade(account=tt_account, date=tt_date, buy_amount=tt_buy_amount,
                         buy_asset=tt_buy_asset, sell_amount=tt_sell_amount,
                         sell_asset=tt_sell_asset, fees=tt_fees, fees_asset=tt_fees_asset,
                         is_move_trade=True)
        to_trade.save()

    # update
    def update_price(self):
        file_path = os.path.join(settings.MEDIA_ROOT, "crypto/prices")
        file_name = time.strftime("%d%m%Y") + ".json"
        file = os.path.join(file_path, file_name)
        if os.path.exists(file):
            with open(file, "r") as file:
                data = json.load(file)
                for entry in data:
                    if entry["symbol"] == self.symbol:
                        data_price = entry["price_" + "eur"]
                        data_time = int(entry["last_updated"])
                        data_time = datetime.fromtimestamp(data_time)
                        data_time = data_time.replace(tzinfo=pytz.utc)
                        if not Price.objects\
                                .filter(asset=self, date=data_time, currency="EUR").exists():
                            price = Price(asset=self, date=data_time, price=data_price,
                                          currency="EUR")
                            price.save()
                        break


class Trade(models.Model):
    account = models.ForeignKey(Account, related_name="trades", on_delete=models.CASCADE)
    date = models.DateTimeField()
    buy_amount = models.DecimalField(max_digits=20, decimal_places=10)
    buy_asset = models.ForeignKey(Asset, related_name="buy_trades", on_delete=models.CASCADE)
    sell_amount = models.DecimalField(max_digits=20, decimal_places=10)
    sell_asset = models.ForeignKey(Asset, related_name="sell_trades", on_delete=models.CASCADE)
    fees = models.DecimalField(max_digits=20, decimal_places=10)
    fees_asset = models.ForeignKey(Asset, related_name="trade_fees", on_delete=models.CASCADE)
    is_move_trade = models.BooleanField(default=False)

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
        return "{} {} {} {} {} {} {} {} ".format(date, account, buy_amount, buy_asset, sell_amount,
                                                 sell_asset, fees, fees_asset)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.buy_asset != self.fees_asset and self.sell_asset != self.fees_asset:
            raise TypeError("The fees asset must be the same as the buy or the sell asset")
        super(Trade, self).save(force_insert, force_update, using, update_fields)


class Timespan(CoreTimespan):
    depot = models.ForeignKey(Depot, editable=False, related_name="timespans",
                              on_delete=models.CASCADE)


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
        if self.depot and self.account and self.asset:
            return str(self.depot) + " with " + str(self.account) + " with " + str(self.asset)
        elif self.depot and self.account and not self.asset:
            return str(self.depot) + " with " + str(self.account)
        elif self.depot and not self.account and self.asset:
            return str(self.depot) + " with " + str(self.asset)
        elif self.depot and not self.account and not self.asset:
            return str(self.depot)
        else:
            return "delete me"

    # getters
    def get_data(self):
        if not self.data:
            data = dict()
            pictures = self.pictures.all()
            data["d"] = (pictures.values_list("d", flat=True))
            data["p"] = (pictures.values_list("p", flat=True))
            data["v"] = (pictures.values_list("v", flat=True))
            data["g"] = (pictures.values_list("g", flat=True))
            data["cr"] = (pictures.values_list("cr", flat=True))
            data["ttwr"] = (pictures.values_list("ttwr", flat=True))
            data["td"] = (pictures.values_list("td", flat=True))
            data["ba"] = (pictures.values_list("ba", flat=True))
            data["bs"] = (pictures.values_list("bs", flat=True))
            data["sa"] = (pictures.values_list("sa", flat=True))
            data["ss"] = (pictures.values_list("ss", flat=True))
            data["ca"] = (pictures.values_list("ca", flat=True))
            data["cs"] = (pictures.values_list("cs", flat=True))
            self.data = data
        return self.data

    def get_timespan_data(self, parent_timespan):
        if not self.timespan_data:
            timespan = parent_timespan.get_timespans().last()
            data = dict()
            if timespan.start_date and timespan.end_date:
                pictures = self.pictures.filter(d__gte=timespan.start_date,
                                                d__lte=timespan.end_date)
                data["d"] = (pictures.values_list("d", flat=True))
                data["p"] = (pictures.values_list("p", flat=True))
                data["v"] = (pictures.values_list("v", flat=True))
                data["g"] = (pictures.values_list("g", flat=True))
                data["cr"] = (pictures.values_list("cr", flat=True))
                data["ttwr"] = (pictures.values_list("ttwr", flat=True))
                data["td"] = (pictures.values_list("td", flat=True))
                data["ba"] = (pictures.values_list("ba", flat=True))
                data["bs"] = (pictures.values_list("bs", flat=True))
                data["sa"] = (pictures.values_list("sa", flat=True))
                data["ss"] = (pictures.values_list("ss", flat=True))
                data["ca"] = (pictures.values_list("ca", flat=True))
                data["cs"] = (pictures.values_list("cs", flat=True))
                self.timespan_data = data
            else:
                self.timespan_data = self.get_data()
        return self.timespan_data

    def get_all(self):
        picture = self.pictures.latest("d")
        data = dict()
        data["price"] = picture.p
        data["amount"] = picture.ca
        data["invested"] = picture.cs
        data["yield"] = picture.cr
        data["true_time_weighted_return"] = picture.ttwr
        data["profit"] = picture.g
        data["value"] = picture.v
        if self.depot.user.get_rounded_numbers:
            for key in data:
                data[key] = round(data[key], 2) if data[key] else "x"
        else:
            for key in data:
                if not data[key]:
                    data[key] = "x"
        return data

    # update
    @staticmethod
    def update_all(depot, force_update=False, disable_update=False):
        if force_update:
            for movie in Movie.objects.filter(depot=depot):
                movie.update_needed = True
                movie.save()

        t1 = time.time()
        for account in depot.accounts.all():
            for asset in Asset.objects.exclude(symbol=depot.user.get_currency_display()):
                movie, created = Movie.objects.get_or_create(depot=depot, account=account,
                                                             asset=asset)
                if movie.update_needed and not disable_update:
                    movie.update()
            movie, created = Movie.objects.get_or_create(depot=depot, account=account,
                                                         asset=None)
            if movie.update_needed and not disable_update:
                movie.update()
        for asset in Asset.objects.exclude(symbol=depot.user.get_currency_display()):
            movie, created = Movie.objects.get_or_create(depot=depot, account=None,
                                                         asset=asset)
            if movie.update_needed and not disable_update:
                movie.update()
        movie, created = Movie.objects.get_or_create(depot=depot, account=None, asset=None)
        if movie.update_needed and not disable_update:
            movie.update()
        t2 = time.time()

        print("This update took", str((t2 - t1) / 60), "minutes.")

    def update(self):
        t1 = time.time()
        Picture.objects.filter(movie=self).delete()

        t2 = time.time()
        if self.asset:
            df = self.calc_asset()
        elif self.account and not self.asset:
            df = self.calc_account()
        elif self.depot:
            df = self.calc_depot()
        else:
            raise Exception("Depot, account or asset must be defined in a movie.")

        t3 = time.time()
        d = df.index.to_datetime()
        v = df["value"]
        cs = df["current_sum"]
        g = df["gain"]
        cr = df["current_return"]
        ttwr = df["true_time_weighted_return"]
        if self.asset:
            p = df["price"]
            ca = df["current_amount"]
            assert len(d) == len(v) == len(cs) == len(g) == len(cr) == len(ttwr) == len(p) == \
                len(ca)
            for i in range(len(d)):
                picture = Picture(movie=self, d=d[i], v=v[i], cs=cs[i], g=g[i], cr=cr[i],
                                  ttwr=ttwr[i], p=p[i], ca=ca[i])
                picture.save()
        else:
            assert len(d) == len(v) == len(cs) == len(g) == len(cr) == len(ttwr)
            for i in range(len(d)):
                picture = Picture(movie=self, d=d[i], v=v[i], cs=cs[i], g=g[i], cr=cr[i],
                                  ttwr=ttwr[i])
                picture.save()

        t4 = time.time()
        self.update_needed = False
        self.save()
        done = len(Movie.objects.filter(update_needed=False))
        all = len(Movie.objects.filter().all())
        print(self, "is up to date.", done, "of", all, "movies are up to date. --Delete time:",
              t2 - t1, "--Calc time:", t3 - t2, "--Save time:", t4 - t3)

    # calc helpers
    @staticmethod
    def ffadd(df, column):
        for i in range(1, len(df[column])):
            df.loc[df.index[i], column] = df[column][i - 1] + df[column][i]

    @staticmethod
    def ffmultiply(df, column):
        for i in range(1, len(df[column])):
            try:
                df.loc[df.index[i], column] = df[column][i - 1] * df[column][i]
            except RuntimeWarning as rw:
                if (abs(df[column][i-1]) == numpy.inf and df[column][i] == 0) \
                        or (df[column][i-1] == 0 and abs(df[column][i]) == numpy.inf):
                    df.loc[df.index[i], column] = numpy.nan
                else:
                    print(df[column][i - 1], df[column][i])
                    raise rw

    @staticmethod
    def calc_fifo(type_column, buy_amount_column, buy_sum_column, fee_sum_column,
                  current_amount_column):
        current_sum_row = numpy.zeros(len(buy_amount_column))
        for i in range(len(buy_amount_column)):
            current_amount = current_amount_column[i]
            if current_amount < 0:
                raise Exception("There was more asset sold than available.")
            current_sum = 0
            for k in reversed(range(0, i + 1)):
                if type_column[k] == "BUY":
                    if k > 0:
                        if current_amount > buy_amount_column[k] - buy_amount_column[k - 1]:
                            current_sum += (buy_sum_column[k] - buy_sum_column[k - 1]) + \
                                           (fee_sum_column[k] - fee_sum_column[k - 1])
                            current_amount -= buy_amount_column[k] - buy_amount_column[k - 1]
                        elif current_amount <= buy_amount_column[k] - buy_amount_column[k - 1]:
                            current_sum += ((buy_sum_column[k] - buy_sum_column[k - 1]) +
                                            (fee_sum_column[k] - fee_sum_column[k - 1])) * \
                                           (current_amount /
                                            (buy_amount_column[k] - buy_amount_column[k - 1]))
                            current_amount -= current_amount
                            break
                    else:
                        if current_amount <= buy_amount_column[k]:
                            current_sum += (buy_sum_column[k] + fee_sum_column[k]) * \
                                           (current_amount / buy_amount_column[k])
                            current_amount -= current_amount
                            break
                        else:
                            raise Exception("Something is wrong here.")
            assert current_amount == 0  # if fails something wrong in the formula
            current_sum_row[i] = Decimal(current_sum)
        return current_sum_row.astype(numpy.float64)

    # calc
    def calc_asset(self):
        price_df = pandas.DataFrame()
        prices = Price.objects.filter(asset=self.asset).order_by("date")
        price_df["date"] = [price.date for price in prices]
        price_df["price"] = [price.price for price in prices]

        if self.account:
            trades = Trade.objects.filter(account=self.account)\
                .filter(Q(sell_asset=self.asset) | Q(buy_asset=self.asset)).order_by("date")
        elif self.depot:
            trades = Trade.objects.filter(account__in=self.depot.accounts.all()) \
                .filter(Q(sell_asset=self.asset) | Q(buy_asset=self.asset)).order_by("date")
        else:
            raise Exception("Something is wrong here.")
        if not self.account:
            adj_trades = list()
            for trade in trades:
                if trade.is_move_trade:
                    trade.buy_amount = 0
                    trade.sell_amount = 0
                adj_trades.append(trade)
            assert len(adj_trades) == len(trades)
            trades = adj_trades

        trade_df = pandas.DataFrame()
        trade_df["date"] = [trade.date for trade in trades]
        trade_df["type"] = ["BUY" if trade.buy_asset == self.asset else "SELL" for trade in trades]
        trade_df["buy_amount"] = [trade.buy_amount if trade.buy_asset == self.asset else 0
                                  for trade in trades]
        Movie.ffadd(trade_df, "buy_amount")
        trade_df["buy_sum"] = [trade.sell_asset.get_worth(trade.date, trade.sell_amount)
                               if trade.buy_asset == self.asset else 0 for trade in trades]
        Movie.ffadd(trade_df, "buy_sum")
        trade_df["sell_amount"] = [trade.sell_amount if trade.sell_asset == self.asset
                                   else 0 for trade in trades]
        Movie.ffadd(trade_df, "sell_amount")
        trade_df["sell_sum"] = [trade.buy_asset.get_worth(trade.date, trade.buy_amount)
                                if trade.sell_asset == self.asset else 0 for trade in trades]
        Movie.ffadd(trade_df, "sell_sum")
        trade_df["fee_amount_sell"] = [trade.fees
                                       if trade.fees_asset == self.asset
                                       and trade.sell_asset == self.asset
                                       else 0 for trade in trades]
        Movie.ffadd(trade_df, "fee_amount_sell")
        trade_df["fee_sum_buy"] = [trade.fees_asset.get_worth(trade.date, trade.fees)
                                   if trade.buy_asset == self.asset else 0 for trade in trades]
        Movie.ffadd(trade_df, "fee_sum_buy")
        trade_df["current_amount"] = \
            trade_df["buy_amount"] - trade_df["sell_amount"] - trade_df["fee_amount_sell"]
        trade_df["current_sum"] = Movie.calc_fifo(trade_df["type"], trade_df["buy_amount"],
                                                  trade_df["buy_sum"], trade_df["fee_sum_buy"],
                                                  trade_df["current_amount"])

        price_df.set_index("date", inplace=True)
        trade_df.set_index("date", inplace=True)
        df = pandas.concat([price_df, trade_df], join="outer", ignore_index=False)
        assert len(price_df) + len(trade_df) == len(df)
        df.drop(columns=["type", ], inplace=True)
        df.sort_index(inplace=True)
        df.ffill(inplace=True)
        for column in df:
            df[column] = df[column].astype(numpy.float64)

        df["value"] = df["current_amount"] * df["price"]
        df["gain"] = df["value"] - df["current_sum"]
        df["current_return"] = ((df["value"].divide(df["current_sum"])) - 1) * 100
        df.fillna(0, inplace=True)
        df["true_time_weighted_return"] = df["value"]\
            .divide((df["value"].shift(1) + (df["current_sum"] - df["current_sum"].shift(1))))
        df["true_time_weighted_return"].replace(numpy.nan, 1, inplace=True)
        Movie.ffmultiply(df, "true_time_weighted_return")
        df["true_time_weighted_return"] = (df["true_time_weighted_return"] - 1) * 100
        df.fillna(0, inplace=True)

        df.replace([numpy.nan, ], 0, inplace=True)  # change later maybe couldn't get django
        #  to acctept inf and nan values on decimal field
        df.replace([numpy.inf, ], 9999999999, inplace=True)  # change later maybe
        df.replace([-numpy.inf, ], -9999999999, inplace=True)  # change later maybe

        # import tabulate
        # print(tabulate.tabulate(df, headers="keys"))
        return df

    def calc_account(self):
        df = pandas.DataFrame()
        df["value"] = ""
        df["current_sum"] = ""

        asset_dfs_length = 0
        asset_dfs_values = list()
        asset_dfs_current_sums = list()

        for asset in Asset.objects.exclude(symbol="EUR"):
            movie = asset.get_acc_movie(self.account)
            data = movie.get_data()

            asset_df = pandas.DataFrame()
            asset_df["date"] = data["d"]
            asset_df.set_index("date", inplace=True)
            asset_df[asset.name + "__value"] = data["v"]
            asset_df[asset.name + "__current_sum"] = data["cs"]

            asset_dfs_values.append(asset.name + "__value")
            asset_dfs_current_sums.append(asset.name + "__current_sum")
            asset_dfs_length += len(asset_df)

            df = pandas.concat([df, asset_df], join="outer", ignore_index=False)

        assert len(df) == asset_dfs_length
        df.sort_index(inplace=True)
        df = df[~df.index.duplicated(keep="last")]
        df.ffill(inplace=True)
        df.fillna(0, inplace=True)
        for column in df:
            df[column] = df[column].astype(numpy.float64)

        for column in asset_dfs_values:
            df["value"] += df[column]
        for column in asset_dfs_current_sums:
            df["current_sum"] += df[column]
        df.drop(columns=asset_dfs_values, inplace=True)
        df.drop(columns=asset_dfs_current_sums, inplace=True)

        df["gain"] = df["value"] - df["current_sum"]
        df["current_return"] = ((df["value"].divide(df["current_sum"])) - 1) * 100
        df["true_time_weighted_return"] = df["value"]\
            .divide((df["value"].shift(1) + (df["current_sum"] - df["current_sum"].shift(1))))
        df["true_time_weighted_return"].replace([numpy.nan, ], 1, inplace=True)
        Movie.ffmultiply(df, "true_time_weighted_return")
        df["true_time_weighted_return"] = (df["true_time_weighted_return"] - 1) * 100
        df.fillna(0, inplace=True)

        # import tabulate
        # print(tabulate.tabulate(df, headers="keys"))
        return df

    def calc_depot(self):
        df = pandas.DataFrame()
        df["value"] = ""
        df["current_sum"] = ""

        asset_dfs_length = 0
        asset_dfs_values = list()
        asset_dfs_current_sums = list()

        for asset in Asset.objects.exclude(symbol="EUR"):
            movie = asset.get_dep_movie(self.depot)
            data = movie.get_data()

            asset_df = pandas.DataFrame()
            asset_df["date"] = data["d"]
            asset_df.set_index("date", inplace=True)
            asset_df[asset.name + "__value"] = data["v"]
            asset_df[asset.name + "__current_sum"] = data["cs"]

            asset_dfs_values.append(asset.name + "__value")
            asset_dfs_current_sums.append(asset.name + "__current_sum")
            asset_dfs_length += len(asset_df)

            df = pandas.concat([df, asset_df], join="outer", ignore_index=False)

        assert len(df) == asset_dfs_length
        df.sort_index(inplace=True)
        df = df[~df.index.duplicated(keep="last")]
        df.ffill(inplace=True)
        df.fillna(0, inplace=True)
        for column in df:
            df[column] = df[column].astype(numpy.float64)

        for column in asset_dfs_values:
            df["value"] += df[column]
        for column in asset_dfs_current_sums:
            df["current_sum"] += df[column]
        df.drop(columns=asset_dfs_values, inplace=True)
        df.drop(columns=asset_dfs_current_sums, inplace=True)

        df["gain"] = df["value"] - df["current_sum"]
        df["current_return"] = ((df["value"].divide(df["current_sum"])) - 1) * 100
        df["true_time_weighted_return"] = df["value"]\
            .divide((df["value"].shift(1) + (df["current_sum"] - df["current_sum"].shift(1))))
        df["true_time_weighted_return"].replace([numpy.nan, ], 1, inplace=True)
        Movie.ffmultiply(df, "true_time_weighted_return")
        df["true_time_weighted_return"] = (df["true_time_weighted_return"] - 1) * 100
        df.fillna(0, inplace=True)

        # import tabulate
        # print(tabulate.tabulate(df, headers="keys"))
        return df


class Picture(models.Model):
    movie = models.ForeignKey(Movie, related_name="pictures", on_delete=models.CASCADE)
    d = models.DateTimeField()

    p = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)
    v = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)
    g = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)
    cr = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)
    ttwr = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)

    td = models.DateTimeField(blank=True, null=True)
    ba = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=8)
    bs = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)
    sa = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=8)
    ss = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)
    ca = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=8)
    cs = models.DecimalField(blank=True, null=True, max_digits=18, decimal_places=3)

    prev = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True)


class Price(models.Model):
    asset = models.ForeignKey(Asset, related_name="prices", on_delete=models.PROTECT)
    date = models.DateTimeField()
    price = models.DecimalField(decimal_places=2, max_digits=15, default=0)
    currency = models.CharField(max_length=3)

    class Meta:
        unique_together = ("asset", "date", "currency")

    def __str__(self):
        asset = str(self.asset)
        date = self.date.strftime("%Y-%m-%d")
        price = str(self.price)
        return asset + " " + date + " " + price

    # getters
    def get_date(self):
        return str(self.date.strftime("%Y-%m-%d %H:%M"))

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
