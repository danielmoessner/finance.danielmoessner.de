from apps.users.models import StandardUser
from apps.core.models import Account as CoreAccount, Depot as CoreDepot
from django.db.models import Sum
from apps.core.utils import change_time_of_date_index_in_df
from django.utils import timezone
from django.db import models
from apps.core import utils
from datetime import timedelta
import apps.core.return_calculation as rc
import pandas as pd


class Depot(CoreDepot):
    user = models.ForeignKey(StandardUser, editable=False, related_name="crypto_depots", on_delete=models.CASCADE)
    # query optimization
    value = models.FloatField(null=True)
    current_return = models.FloatField(null=True)
    invested_capital = models.FloatField(null=True)
    time_weighted_return = models.FloatField(null=True)
    internal_rate_of_return = models.FloatField(null=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        if not self.assets.filter(symbol='EUR').exists():
            self.assets.create(symbol='EUR')
        if self.is_active:
            self.user.crypto_depots.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)

    # getters
    def get_flow_df(self):
        if not hasattr(self, 'flow_df'):
            # get the flow df
            df = pd.DataFrame(data=list(Flow.objects.filter(account__in=self.accounts.all()).values('date', 'flow')),
                              columns=['date', 'flow'])
            df.set_index('date', inplace=True)
            # make it to float so that pandas can calculate everything, decimal doesn't work fine with pandas
            df.loc[:, 'flow'] = df.loc[:, 'flow'].apply(pd.to_numeric, downcast='float')
            # make the time to the same as in the value df: 12:00, in order to calculate everything correctly
            df = change_time_of_date_index_in_df(df, 12)
            # combine the duplicates to a single flow
            df = df.groupby(by='date').sum()
            # set the df
            self.flow_df = df
        return self.flow_df

    def get_value_df(self):
        if not hasattr(self, 'value_df'):
            self.value_df = utils.sum_up_value_dfs_from_items(self.assets.all())
        return self.value_df

    def get_value(self):
        if self.value is None:
            self.value = 0
            for asset in list(self.assets.all()):
                self.value += float(asset.get_value())
            self.save()
        return self.value

    def get_invested_capital(self):
        if self.invested_capital is None:
            df = rc.get_current_return_df(self.get_flow_df(), self.get_value_df())
            self.invested_capital = rc.get_invested_capital(df)
            self.save()
        return self.invested_capital

    def get_time_weighted_return(self):
        if self.time_weighted_return is None:
            df = rc.get_time_weighted_return_df(self.get_flow_df(), self.get_value_df())
            self.time_weighted_return = rc.get_time_weighted_return(df)
            self.save()
        return self.time_weighted_return

    def get_current_return(self):
        if self.current_return is None:
            df = rc.get_current_return_df(self.get_flow_df(), self.get_value_df())
            self.current_return = rc.get_current_return(df)
            self.save()
        return self.current_return

    def get_internal_rate_of_return(self):
        if self.internal_rate_of_return is None:
            df = rc.get_internal_rate_of_return_df(self.get_flow_df(), self.get_value_df())
            self.internal_rate_of_return = rc.get_internal_rate_of_return(df)
            self.save()
        return self.internal_rate_of_return

    def get_stats(self):
        return {
            'Value': self.get_value(),
            'Invested Capital': self.get_invested_capital(),
            'Time Weighted Return': self.get_time_weighted_return(),
            'Current Return': self.get_current_return(),
            'Internal Rate of Return': self.get_internal_rate_of_return()
        }

    # setters
    def reset_all(self):
        Depot.objects.filter(pk=self.pk).update(value=None, internal_rate_of_return=None, invested_capital=None,
                                                time_weighted_return=None, current_return=None)
        Asset.objects.filter(depot=self).update(value=None, amount=None, price=None)
        Account.objects.filter(depot=self).update(value=None)
        AccountAssetStats.objects.filter(account__in=self.accounts.all()).update(value=None, amount=None)


class Account(CoreAccount):
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name="accounts")
    # query optimization
    value = models.FloatField(null=True)

    # getters
    def get_stats(self):
        return {
            'Value': self.get_value()
        }

    def get_value(self):
        if self.value is None:
            # create all asset stats so that the calculated data is correct
            if self.asset_stats.all().count() != self.depot.assets.all().count():
                for asset in self.depot.assets.all():
                    AccountAssetStats.objects.get_or_create(asset=asset, account=self)
            # sum up the values
            self.value = 0
            for stats in list(self.asset_stats.select_related('asset', 'account')):
                self.value += stats.get_value()
            self.save()
        return self.value

    def get_asset_stats(self, asset):
        stats, created = AccountAssetStats.objects.get_or_create(asset=asset, account=self)
        return stats

    def get_value_asset(self, asset):
        stats = self.get_asset_stats(asset)
        return stats.get_value()

    def get_amount_asset(self, asset):
        stats = self.get_asset_stats(asset)
        return stats.get_amount()

    def get_amount_asset_before_date(self, asset, date, exclude_transactions=None, exclude_trades=None,
                                     exclude_flows=None):
        stats = self.get_asset_stats(asset)
        return stats.get_amount_before_date(date, exclude_trades=exclude_trades, exclude_flows=exclude_flows,
                                            exclude_transactions=exclude_transactions)


class Asset(models.Model):
    symbol = models.CharField(max_length=5)
    depot = models.ForeignKey(Depot, related_name='assets', on_delete=models.CASCADE)
    # query optimization
    value = models.FloatField(null=True)
    amount = models.FloatField(null=True)
    price = models.FloatField(null=True)

    def __str__(self):
        return '{}'.format(self.symbol)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # uppercase the symbol for convenience
        self.symbol = self.symbol.upper()
        super().save(force_update=force_update, force_insert=force_insert, using=using, update_fields=update_fields)
        # test that there is a price for the euro asset or the base asset which is euro in this case
        if self.symbol == 'EUR' and not Price.objects.filter(symbol='EUR').exists():
            Price.objects.create(symbol='EUR', price=1, date=timezone.now())

    # getters
    def get_price_df(self):
        # get all prices
        df = pd.DataFrame(data=list(Price.objects.filter(symbol=self.symbol).values('date', 'price')),
                          columns=['date', 'price'])
        df.set_index('date', inplace=True)
        # print(df)
        # return none if there is nothing to be calculated
        if df.empty:
            return None
        # make it float so that everything with pandas work, for example interpolate doesn't work with decimal
        df.loc[:, 'price'] = df.loc[:, 'price'].apply(pd.to_numeric, downcast='float')
        # remove the time; we need this because of the merging of the value dfs in the depot get_value_df function
        df = change_time_of_date_index_in_df(df, 12)
        # drop duplicates as asfreq will throw an error if duplicates exist and sort
        df = df.groupby(df.index, sort=True).tail(1)
        # return the df
        return df

    def get_value_df(self):
        return utils.create_value_df_from_amount_and_price(self)

    def get_amount_df(self):
        # get all possible amount changing objects
        trade_buy_df = pd.DataFrame(data=list(Trade.objects.filter(buy_asset=self).values('date', 'buy_amount')),
                                    columns=['date', 'buy_amount'])
        trade_sell_df = pd.DataFrame(data=list(Trade.objects.filter(sell_asset=self).values('date', 'sell_amount')),
                                     columns=['date', 'sell_amount'])
        transaction_fees_df = pd.DataFrame(data=list(Transaction.objects.filter(asset=self).values('date', 'fees')),
                                           columns=['date', 'fees'])
        flow_df = pd.DataFrame(data=list(Flow.objects.filter(asset=self).values('date', 'flow')),
                               columns=['date', 'flow'])
        # merge everything into a big dataframe
        df = pd.merge(trade_buy_df, trade_sell_df, how='outer', on='date', sort=True)
        df = df.merge(transaction_fees_df, how='outer', on='date', sort=True)
        df = df.merge(flow_df, how='outer', on='date', sort=True)
        # return none if the df is empty
        if df.empty:
            return None
        # set index
        df.set_index('date', inplace=True)
        # replace nan with 0
        df = df.fillna(0)
        # calculate the change on each date
        df.loc[:, 'change'] = df.loc[:, 'buy_amount'] - df.loc[:, 'sell_amount'] - df.loc[:, 'fees'] + df.loc[:, 'flow']
        # the amount is the sum of all changes
        df.loc[:, 'amount'] = df.loc[:, 'change'].cumsum()
        # make the df smaller
        df = df.loc[:, ['amount']]
        # cast to float otherwise pandas can not reliably use all methods for example interpolate wouldn't work
        df.loc[:, 'amount'] = df.loc[:, 'amount'].apply(pd.to_numeric, downcast='float')
        # set a standard time for easir calculations and group by date
        df = change_time_of_date_index_in_df(df, 12)
        df = df.groupby(df.index, sort=True).tail(1)
        # return the df
        return df

    def get_stats(self):
        return {
            'Amount': self.get_amount(),
            'Value': self.get_value()
        }

    def get_price(self):
        if self.price is None:
            price = Price.objects.filter(symbol=self.symbol).order_by('date').last()
            if price is not None:
                self.price = price.price or 0
            else:
                self.price = 0
            self.save()
        return self.price

    def get_value(self):
        if self.value is None:
            amount = self.get_amount()
            price = self.get_price()
            self.value = float(amount) * float(price)
            self.save()
        return self.value

    def get_account_stats(self, account):
        stats, created = AccountAssetStats.objects.get_or_create(asset=self, account=account)
        return stats

    def get_value_account(self, account):
        stats = self.get_account_stats(account)
        return stats.get_value()

    def get_amount_account(self, account):
        stats = self.get_account_stats(account)
        return stats.get_amount()

    def get_amount(self):
        if self.amount is None:
            trade_buy_amount = (Trade.objects
                                .filter(buy_asset=self, account__in=self.depot.accounts.all())
                                .aggregate(Sum('buy_amount'))['buy_amount__sum'] or 0)
            trade_sell_amount = (Trade.objects
                                 .filter(sell_asset=self, account__in=self.depot.accounts.all())
                                 .aggregate(Sum('sell_amount'))['sell_amount__sum'] or 0)
            transaction_fees_amount = (Transaction.objects
                                       .filter(asset=self, from_account__in=self.depot.accounts.all())
                                       .aggregate(Sum('fees'))['fees__sum'] or 0)
            flow_amount = (Flow.objects
                           .filter(asset=self)
                           .aggregate(Sum('flow'))['flow__sum'] or 0)
            self.amount = trade_buy_amount - trade_sell_amount - transaction_fees_amount + flow_amount
            self.save()
        return self.amount


class AccountAssetStats(models.Model):
    account = models.ForeignKey(Account, related_name='asset_stats', on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, related_name='account_stats', on_delete=models.CASCADE)
    # query optimization
    amount = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    value = models.FloatField(null=True)

    # getters
    def get_amount(self):
        if self.amount is None:
            trade_buy_amount = (Trade.objects
                                .filter(buy_asset=self.asset, account=self.account)
                                .aggregate(Sum('buy_amount'))['buy_amount__sum'] or 0)
            trade_sell_amount = (Trade.objects
                                 .filter(sell_asset=self.asset, account=self.account)
                                 .aggregate(Sum('sell_amount'))['sell_amount__sum'] or 0)
            transaction_to_amount = (Transaction.objects
                                     .filter(asset=self.asset, to_account=self.account)
                                     .aggregate(Sum('amount'))['amount__sum'] or 0)
            transaction_from_and_fees_amount = (Transaction.objects
                                                .filter(asset=self.asset, from_account=self.account)
                                                .aggregate(Sum('fees'), Sum('amount')))
            flow_amount = (Flow.objects
                           .filter(asset=self.asset, account=self.account)
                           .aggregate(Sum('flow'))['flow__sum'] or 0)
            transaction_from_amount = transaction_from_and_fees_amount['amount__sum'] or 0
            transaction_fees_amount = transaction_from_and_fees_amount['fees__sum'] or 0
            trade_amount = trade_buy_amount - trade_sell_amount
            transaction_amount = transaction_to_amount - transaction_fees_amount - transaction_from_amount
            self.amount = trade_amount + transaction_amount + flow_amount
            self.save()
        return self.amount

    def get_amount_before_date(self, date, exclude_transactions=None, exclude_trades=None, exclude_flows=None):
        if exclude_trades is None:
            exclude_trades = []
        if exclude_transactions is None:
            exclude_transactions = []
        if exclude_flows is None:
            exclude_flows = []

        trade_buy_amount = (Trade.objects
                            .filter(buy_asset=self.asset, account=self.account, date__lt=date)
                            .exclude(pk__in=exclude_trades)
                            .aggregate(Sum('buy_amount'))['buy_amount__sum'] or 0)
        trade_sell_amount = (Trade.objects
                             .filter(sell_asset=self.asset, account=self.account, date__lt=date)
                             .exclude(pk__in=exclude_trades)
                             .aggregate(Sum('sell_amount'))['sell_amount__sum'] or 0)
        transaction_to_amount = (Transaction.objects
                                 .filter(asset=self.asset, to_account=self.account, date__lt=date)
                                 .exclude(pk__in=exclude_transactions)
                                 .aggregate(Sum('amount'))['amount__sum'] or 0)
        transaction_from_and_fees_amount = (Transaction.objects
                                            .filter(asset=self.asset, from_account=self.account, date__lt=date)
                                            .exclude(pk__in=exclude_transactions)
                                            .aggregate(Sum('fees'), Sum('amount')))
        flow_amount = (Flow.objects
                       .filter(asset=self.asset, account=self.account, date__lt=date)
                       .exclude(pk__in=exclude_flows)
                       .aggregate(Sum('flow'))['flow__sum'] or 0)
        transaction_from_amount = transaction_from_and_fees_amount['amount__sum'] or 0
        transaction_fees_amount = transaction_from_and_fees_amount['fees__sum'] or 0
        trade_amount = trade_buy_amount - trade_sell_amount
        transaction_amount = transaction_to_amount - transaction_fees_amount - transaction_from_amount
        amount = trade_amount + transaction_amount + flow_amount
        return amount

    def get_value(self):
        if self.value is None:
            amount = float(self.get_amount())
            price = float(self.asset.get_price())
            self.value = amount * price
            self.save()
        return self.value


class Trade(models.Model):
    account = models.ForeignKey(Account, related_name="trades", on_delete=models.PROTECT)
    date = models.DateTimeField()
    buy_amount = models.DecimalField(max_digits=20, decimal_places=8)
    buy_asset = models.ForeignKey(Asset, related_name="buy_trades", on_delete=models.PROTECT)
    sell_amount = models.DecimalField(max_digits=20, decimal_places=8)
    sell_asset = models.ForeignKey(Asset, related_name="sell_trades", on_delete=models.PROTECT)

    class Meta:
        ordering = ["-date"]
        unique_together = ('account', 'date')

    def __str__(self):
        account = str(self.account)
        date = str(self.date.date())
        buy_asset = str(self.buy_asset)
        buy_amount = str(self.buy_amount)
        sell_asset = str(self.sell_asset)
        sell_amount = str(self.sell_amount)
        return "{} {} {} {} {} {}".format(self.get_date(), account, buy_amount, buy_asset, sell_amount, sell_asset)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        self.account.depot.reset_all()

    def delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)
        self.account.depot.reset_all()

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y %H:%M")


class Transaction(models.Model):
    asset = models.ForeignKey(Asset, related_name="transactions", on_delete=models.PROTECT)
    from_account = models.ForeignKey(Account, related_name="from_transactions", on_delete=models.PROTECT)
    date = models.DateTimeField()
    to_account = models.ForeignKey(Account, related_name="to_transactions", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    fees = models.DecimalField(max_digits=20, decimal_places=8)

    class Meta:
        unique_together = (('from_account', 'date'), ('to_account', 'date'))

    def __str__(self):
        return '{} {} {} {} {}'.format(self.asset, self.date, self.from_account, self.to_account, self.amount)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        self.asset.depot.reset_all()

    def delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)
        self.asset.depot.reset_all()

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y %H:%M")


class Price(models.Model):
    symbol = models.CharField(max_length=5, null=True)
    date = models.DateTimeField()
    price = models.DecimalField(decimal_places=2, max_digits=15, default=0)

    class Meta:
        unique_together = ("symbol", "date")

    def __str__(self):
        return "{} {} {}".format(self.symbol, self.get_date(), self.price)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if Price.objects.filter(symbol=self.symbol,
                                date__gte=(self.date - timedelta(hours=23)),
                                date__lte=self.date).exists():
            return
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        [asset.depot.reset_all() for asset in Asset.objects.filter(symbol=self.symbol)]

    def delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)
        [asset.depot.reset_all() for asset in Asset.objects.filter(symbol=self.symbol)]

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%Y")


class Flow(models.Model):
    account = models.ForeignKey(Account, related_name='flows', on_delete=models.CASCADE)
    date = models.DateTimeField()
    flow = models.DecimalField(max_digits=20, decimal_places=2)
    asset = models.ForeignKey(Asset, related_name='flows', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('account', 'date')

    def __str__(self):
        return '{} {} {}'.format(self.get_date(), self.account, self.flow)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        self.account.depot.reset_all()

    def delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)
        self.account.depot.reset_all()

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime('%d.%m.%Y %H:%M')


class CoinGeckoAsset(models.Model):
    symbol = models.CharField(max_length=5, unique=True)
    coingecko_symbol = models.CharField(max_length=10)
    coingecko_id = models.CharField(max_length=40, unique=True)
