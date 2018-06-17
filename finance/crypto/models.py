from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.conf import settings
from django.db import models

from finance.users.models import StandardUser
from finance.core.models import Timespan as CoreTimespan
from finance.core.models import Account as CoreAccount
from finance.core.models import Depot as CoreDepot
from finance.core.utils import create_slug

from datetime import datetime
from decimal import Decimal
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
        return price * amount

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
    amount = models.DecimalField(max_digits=20, decimal_places=10)
    fees = models.DecimalField(max_digits=20, decimal_places=10)


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
        pictures = pictures.values(
            "d", "p", "v", "g", "cr", "ttwr", "td", "ba", "bs", "sa", "ss", "ca", "cs")
        df = pd.DataFrame(list(pictures))
        if df.empty:
            df = pd.DataFrame(columns=["d", "p", "v", "g", "cr", "ttwr", "td", "ba", "bs", "sa",
                                       "ss", "ca", "cs"])
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
        data["td"] = (pictures.values_list("td", flat=True))
        data["ba"] = (pictures.values_list("ba", flat=True))
        data["bs"] = (pictures.values_list("bs", flat=True))
        data["sa"] = (pictures.values_list("sa", flat=True))
        data["ss"] = (pictures.values_list("ss", flat=True))
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
        self.pictures.all().delete()

        t2 = time.time()
        if self.depot and not self.account and self.asset:
            df = self.calc_asset_depot()
        elif self.depot and self.account and self.asset:
            df = self.calc_asset_account()
        elif self.depot and self.account and not self.asset:
            df = self.calc_account()
        elif self.depot and not self.account and not self.asset:
            df = self.calc_depot()
        else:
            raise Exception("Depot, account or asset must be defined in a movie.")

        t3 = time.time()
        pictures = list()
        if self.asset and self.account:
            for index, row in df.iterrows():
                picture = Picture(
                    movie=self,
                    d=index,
                    v=row["value"],
                    p=row["price"],
                    ca=row["current_amount"]
                )
                pictures.append(picture)
        elif self.asset and self.depot:
            for index, row in df.iterrows():
                picture = Picture(
                    movie=self,
                    d=index,
                    v=row["value"],
                    cs=row["current_sum"],
                    g=row["gain"],
                    cr=row["current_return"],
                    ttwr=row["true_time_weighted_return"],
                    p=row["price"],
                    ca=row["current_amount"]
                )
                pictures.append(picture)
        elif self.account:
            for index, row in df.iterrows():
                picture = Picture(
                    movie=self,
                    d=index,
                    v=row["value"],
                )
                pictures.append(picture)
        elif self.depot:
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
        text = "{} is up to date. --Calc Time: {}% --Save/Delete Time: {}%".format(
            self, round((t3 - t2) / (t4 - t1), 2), round((t4 - t3 + t2 - t1) / (t4 - t1), 2), "%")
        print(text)
        self.update_needed = False
        self.save()

    # calc helpers
    @staticmethod
    def ffadd(df, column):
        for i in range(1, len(df[column])):
            df.loc[df.index[i], column] = \
                df.loc[df.index[i-1], column] + df.loc[df.index[i], column]

    @staticmethod
    def ffmultiply(df, column):
        for i in range(1, len(df[column])):
            try:
                df.loc[df.index[i], column] = df[column][i - 1] * df[column][i]
            except RuntimeWarning as rw:
                if (abs(df[column][i-1]) == np.inf and df[column][i] == 0) \
                        or (df[column][i-1] == 0 and abs(df[column][i]) == np.inf):
                    df.loc[df.index[i], column] = np.nan
                else:
                    print(df[column][i - 1], df[column][i])
                    raise rw

    @staticmethod
    def calc_fifo(type_column, buy_amount_column, buy_sum_column, fee_sum_column,
                  current_amount_column):
        """
        ATTENTION: The index of the columns must be in ascendent order. Otherwise it doesn't work.
        """
        current_sum_row = np.zeros(len(buy_amount_column))
        for i in range(len(buy_amount_column)):
            current_amount = current_amount_column[i]
            if current_amount < 0:
                raise Exception("There was more asset sold than available.")
            current_sum = 0
            for k in reversed(range(0, i + 1)):  # genauere datetypen hier verwenden numpy iwas
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
        return current_sum_row.astype(np.float64)

    # calc
    def calc_asset_depot(self):
        buy_trades = Trade.objects.filter(buy_asset=self.asset)
        buy_trades_values = buy_trades.values("date", "buy_amount")
        buy_trades_df = pd.DataFrame(list(buy_trades_values))
        buy_trades_df["type"] = "BUY"
        buy_trades_df["buy_sum"] = [trade.sell_asset.get_worth(trade.date, trade.sell_amount) for
                                    trade in buy_trades]
        buy_trades_df["fee_sum_buy"] = [trade.fees_asset.get_worth(trade.date, trade.fees)
                                        for trade in buy_trades]
        if buy_trades_df.empty:
            buy_trades_df = pd.DataFrame(columns=["date", "buy_amount", "type", "buy_sum",
                                                  "fee_sum_buy"])

        sell_trades = Trade.objects.filter(sell_asset=self.asset)
        sell_trades_values = sell_trades.values("date", "sell_amount")
        sell_trades_df = pd.DataFrame(list(sell_trades_values))
        sell_trades_df["type"] = "SELL"
        sell_trades_df["sell_sum"] = [trade.buy_asset.get_worth(trade.date, trade.buy_amount)
                                      for trade in sell_trades]
        sell_trades_df["fee_amount_sell"] = [Decimal(trade.fees) if trade.fees_asset == self.asset
                                             else Decimal(0) for trade in sell_trades]
        if sell_trades_df.empty:
            sell_trades_df = pd.DataFrame(columns=["date", "sell_amount", "type", "sell_sum",
                                                   "fee_amount_sell"])

        transactions = Transaction.objects.filter(asset=self.asset)
        transactions = transactions.values("date", "fees")
        transactions_df = pd.DataFrame(list(transactions))
        transactions_df["type"] = "TRANSACTION"
        if transactions_df.empty:
            transactions_df = pd.DataFrame(columns=["date", "fees", "type"])

        tratra_df = pd.concat([buy_trades_df, sell_trades_df, transactions_df],
                              join="outer", ignore_index=True, sort=False)
        tratra_df.fillna(Decimal(0), inplace=True)
        tratra_df["fee_amount"] = tratra_df["fee_amount_sell"] + tratra_df["fees"]
        tratra_df.sort_values(by=["date"], inplace=True)
        Movie.ffadd(tratra_df, "buy_amount")
        Movie.ffadd(tratra_df, "buy_sum")
        Movie.ffadd(tratra_df, "sell_amount")
        Movie.ffadd(tratra_df, "sell_sum")
        Movie.ffadd(tratra_df, "fee_amount")
        Movie.ffadd(tratra_df, "fee_sum_buy")
        tratra_df = tratra_df[tratra_df.type != "TRANSACTION"]
        tratra_df.reset_index(drop=True, inplace=True)
        tratra_df["current_amount"] = \
            tratra_df["buy_amount"] - tratra_df["sell_amount"] - tratra_df["fee_amount"]
        tratra_df["current_sum"] = Movie.calc_fifo(tratra_df["type"], tratra_df["buy_amount"],
                                                   tratra_df["buy_sum"], tratra_df["fee_sum_buy"],
                                                   tratra_df["current_amount"])

        prices = Price.objects.filter(asset=self.asset)
        prices = prices.values("date", "price")
        price_df = pd.DataFrame(list(prices))

        price_df.set_index("date", inplace=True)
        tratra_df.set_index("date", inplace=True)
        df = pd.concat([price_df, tratra_df], join="outer", axis=0, ignore_index=False, sort=False)
        df.drop(columns=["type", ], inplace=True)
        df.sort_index(inplace=True)
        df.ffill(inplace=True)
        for column in df:
            df[column] = df[column].astype(np.float64)

        df["value"] = df["current_amount"] * df["price"]
        df["gain"] = df["value"] - df["current_sum"]
        df["current_return"] = ((df["value"].divide(df["current_sum"])) - 1) * 100
        df.fillna(0, inplace=True)
        df["true_time_weighted_return"] = df["value"]\
            .divide((df["value"].shift(1) + (df["current_sum"] - df["current_sum"].shift(1))))
        df["true_time_weighted_return"].replace(np.nan, 1, inplace=True)
        Movie.ffmultiply(df, "true_time_weighted_return")
        df["true_time_weighted_return"] = (df["true_time_weighted_return"] - 1) * 100
        df.fillna(0, inplace=True)

        df.replace([np.nan, ], 0, inplace=True)  # change later maybe couldn't get django
        #  to acctept inf and nan values on decimal field
        df.replace([np.inf, ], 9999999999, inplace=True)  # change later maybe
        df.replace([-np.inf, ], -9999999999, inplace=True)  # change later maybe

        return df

    def calc_asset_account(self):
        # buy trades
        buy_trades = Trade.objects.filter(buy_asset=self.asset, account=self.account)
        buy_trades_values = buy_trades.values("date", "buy_amount")
        buy_trades_df = pd.DataFrame(list(buy_trades_values))
        if buy_trades_df.empty:
            buy_trades_df = pd.DataFrame(columns=["date", "buy_amount"])
        buy_trades_df.set_index("date", inplace=True)
        
        # sell trades
        sell_trades = Trade.objects.filter(sell_asset=self.asset, account=self.account)
        sell_trades_values = sell_trades.values("date", "sell_amount")
        sell_trades_df = pd.DataFrame(list(sell_trades_values))
        sell_trades_df["fee_amount_sell"] = [Decimal(trade.fees) if trade.fees_asset == self.asset
                                             else Decimal(0) for trade in sell_trades]
        if sell_trades_df.empty:
            sell_trades_df = pd.DataFrame(columns=["date", "sell_amount", "fee_amount_sell"])
        sell_trades_df.set_index("date", inplace=True)
        
        # to_transactions
        to_transactions = Transaction.objects.filter(asset=self.asset, to_account=self.account)
        to_transactions = to_transactions.values("date", "amount")
        to_transactions_df = pd.DataFrame(list(to_transactions))
        to_transactions_df.rename(columns={"amount": "to_amount"}, inplace=True)
        if to_transactions_df.empty:
            to_transactions_df = pd.DataFrame(columns=["date", "to_amount"])
        to_transactions_df.set_index("date", inplace=True)

        # from_transactions
        from_transactions = Transaction.objects.filter(asset=self.asset, from_account=self.account)
        from_transactions = from_transactions.values("date", "fees", "amount")
        from_transactions_df = pd.DataFrame(list(from_transactions))
        from_transactions_df.rename(columns={"amount": "from_amount"}, inplace=True)
        if from_transactions_df.empty:
            from_transactions_df = pd.DataFrame(columns=["date", "fees", "from_amount"])
        from_transactions_df.set_index("date", inplace=True)
        
        # buy_trades, sell_trades, to_transactions and from_transactions
        tratra_df = pd.concat([buy_trades_df, sell_trades_df,
                               from_transactions_df, to_transactions_df],
                              join="outer", ignore_index=False, sort=False)
        tratra_df.fillna(Decimal(0), inplace=True)
        tratra_df["fee_amount"] = tratra_df["fee_amount_sell"] + tratra_df["fees"]
        tratra_df.sort_index(inplace=True)
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
        price_df = pd.DataFrame(list(prices))
        price_df.set_index("date", inplace=True)

        # all together
        df = pd.concat([tratra_df, price_df], sort=False)
        df.sort_index(inplace=True)
        df.ffill(inplace=True)
        df.fillna(Decimal(0), inplace=True)
        df["value"] = df["current_amount"] * df["price"]

        return df

    def calc_account(self):
        df = pd.DataFrame(columns=["value", ])
        asset_dfs_values = list()
        
        for asset in self.depot.assets.exclude(symbol="EUR"):
            movie = asset.get_acc_movie(self.account)

            asset_df = movie.get_df()
            asset_df = asset_df[["v", "d"]]
            asset_df.rename(columns={"v": asset.name + "__value", "d": "date"}, inplace=True)
            asset_df.set_index("date", inplace=True)
            asset_dfs_values.append(asset.name + "__value")

            df = pd.concat([df, asset_df], join="outer", ignore_index=False, sort=False)

        df.sort_index(inplace=True)
        df.ffill(inplace=True)
        df.fillna(Decimal(0), inplace=True)

        df = df[~df.index.duplicated(keep="last")]
        for column in asset_dfs_values:
            df["value"] += df[column]
        df.drop(columns=asset_dfs_values, inplace=True)
        df.fillna(0, inplace=True)

        return df

    def calc_depot(self):
        df = pd.DataFrame()
        df["value"] = ""
        df["current_sum"] = ""

        asset_dfs_values = list()
        asset_dfs_current_sums = list()

        for asset in self.depot.assets.exclude(symbol="EUR"):
            movie = asset.get_movie()

            asset_df = movie.get_df()
            asset_df = asset_df[["v", "d", "cs"]]
            asset_df.rename(columns={"v": asset.name + "__value", "d": "date",
                                     "cs": asset.name + "__current_sum"}, inplace=True)
            asset_df.set_index("date", inplace=True)
            asset_dfs_values.append(asset.name + "__value")
            asset_dfs_current_sums.append(asset.name + "__current_sum")

            df = pd.concat([df, asset_df], join="outer", ignore_index=False, sort=False)

        df.sort_index(inplace=True)
        df = df[~df.index.duplicated(keep="last")]
        df.ffill(inplace=True)
        df.fillna(0, inplace=True)
        for column in df:
            df[column] = df[column].astype(np.float64)

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
        df["true_time_weighted_return"].replace([np.nan, ], 1, inplace=True)
        Movie.ffmultiply(df, "true_time_weighted_return")
        df["true_time_weighted_return"] = (df["true_time_weighted_return"] - 1) * 100
        df.fillna(0, inplace=True)

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
