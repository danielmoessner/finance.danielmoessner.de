from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db import models

from finance.users.models import StandardUser
from finance.core.models import Timespan as CoreTimespan
from finance.core.models import Account as CoreAccount
from finance.core.models import Depot as CoreDepot
from finance.core.utils import create_slug

from datetime import datetime
import pandas as pd
import numpy as np
import urllib.request
import urllib.error
import pytz
import time
import json
import os


def init_crypto(user):
    pass


class Depot(CoreDepot):
    user = models.ForeignKey(StandardUser, editable=False, related_name="crypto_depots",
                             on_delete=models.CASCADE)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super(Depot, self).save(force_insert, force_update, using, update_fields)
        Movie.update_all(depot=self, disable_update=True)

    # getters
    def get_movie(self):
        return self.movies.get(account=None, asset=None)

    # update
    def update_prices(self):
        file_path = os.path.join(settings.MEDIA_ROOT, "crypto/prices")
        file_name = time.strftime("%Y%m%d") + ".json"
        file = os.path.join(file_path, file_name)
        if not os.path.exists(file):
            try:
                with urllib.request.urlopen("https://api.coinmarketcap.com/v1/ticker/?convert=" +
                                            self.user.get_currency_display()) as url:
                    data = json.loads(url.read().decode())
                    file_path = os.path.join(settings.MEDIA_ROOT, "crypto/prices")
                    file_name = time.strftime("%Y%m%d") + ".json"
                    file = os.path.join(file_path, file_name)
                    with open(file, "w+") as file:
                        json.dump(data, file)
            except urllib.error.HTTPError:
                return  # error correction
        for asset in Asset.objects.all():
            asset.update_price()


class Account(CoreAccount):
    depot = models.ForeignKey(Depot, on_delete=models.PROTECT, related_name="accounts")

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super(Account, self).save(force_insert, force_update, using, update_fields)
        Movie.update_all(self.depot, disable_update=True)

    # getters
    def get_movie(self):
        return self.movies.get(depot=self.depot, asset=None)


class Asset(models.Model):
    name = models.CharField(max_length=300)
    symbol = models.CharField(max_length=5, unique=True)
    slug = models.SlugField(unique=True)
    depot = models.ForeignKey(Depot, on_delete=models.PROTECT, related_name="assets")

    def __str__(self):
        return str(self.symbol)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.slug:
            self.slug = create_slug(self)
        super(Asset, self).save(force_insert, force_update, using, update_fields)
        Movie.update_all(depot=self.depot, disable_update=True)

    # getters
    def get_movie(self):
        return self.movies.get(depot=self.depot, account=None)

    def get_acc_movie(self, account):
        return self.movies.get(depot=self.depot, account=account)

    def get_worth(self, date, amount):
        prices = Price.objects.filter(asset=self)
        dates = [price.date for price in prices]
        closest_date = min(dates, key=lambda d: abs(d - date))
        index = dates.index(closest_date)
        price = prices[index].price
        return float(price * amount)

    # update
    def update_price(self):
        file_path = os.path.join(settings.MEDIA_ROOT, "crypto/prices")
        file_name = time.strftime("%Y%m%d") + ".json"
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

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.buy_asset != self.fees_asset and self.sell_asset != self.fees_asset:
            raise TypeError("The fees asset must be the same as the buy or the sell asset")
        super(Trade, self).save(force_insert, force_update, using, update_fields)


class Transaction(models.Model):
    asset = models.ForeignKey(Asset, related_name="transactions", on_delete=models.CASCADE)
    from_account = models.ForeignKey(Account, related_name="from_transactions",
                                     on_delete=models.CASCADE)
    date = models.DateTimeField()
    to_account = models.ForeignKey(Account, related_name="to_transactions",
                                   on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    fees = models.DecimalField(max_digits=20, decimal_places=8)


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
    def update_all(depot, force_update=False, disable_update=False):
        if force_update:
            depot.movies.update(update_needed=True)

        t1 = time.time()
        for account in depot.accounts.all():
            for asset in depot.assets.exclude(symbol=depot.user.get_currency_display()):
                movie, created = Movie.objects.get_or_create(depot=depot, account=account,
                                                             asset=asset)
                if movie.update_needed and not disable_update:
                    movie.update()
            movie, created = Movie.objects.get_or_create(depot=depot, account=account, asset=None)
            if movie.update_needed and not disable_update:
                movie.update()
        for asset in depot.assets.exclude(symbol=depot.user.get_currency_display()):
            movie, created = Movie.objects.get_or_create(depot=depot, account=None, asset=asset)
            if movie.update_needed and not disable_update:
                movie.update()
        movie, created = Movie.objects.get_or_create(depot=depot, account=None, asset=None)
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
            from finance.core.utils import print_df
            print_df(df)
            print_df(old_df)
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
            movie = asset.get_acc_movie(self.account)
            asset_df = movie.get_df()
            asset_df = asset_df[["v", "d"]]
            asset_df.rename(columns={"v": asset.name + "__value", "d": "date"}, inplace=True)
            asset_dfs_values.append(asset.name + "__value")
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
            movie = asset.get_movie()
            asset_df = movie.get_df()
            asset_df = asset_df[["v", "d", "cs"]]
            asset_df.rename(columns={"v": asset.name + "__value", "d": "date",
                                     "cs": asset.name + "__current_sum"}, inplace=True)
            asset_dfs_values.append(asset.name + "__value")
            asset_dfs_current_sums.append(asset.name + "__current_sum")
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
