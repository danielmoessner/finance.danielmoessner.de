import random
from datetime import timedelta
from typing import TYPE_CHECKING, Union

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import models
from django.utils import timezone

if TYPE_CHECKING:
    from django.db.models.query import QuerySet

    from apps.alternative.models import Depot as AlternativeDepot
    from apps.banking.models import Depot as BankingDepot
    from apps.crypto.models import Depot as CryptoDepto
    from apps.stocks.models import Depot as StockDepot
    from apps.overview.models import Bucket

class StandardUser(AbstractUser):
    # general
    DATE_FORMAT_CHOICES = (
        ("%d.%m.%Y", "Date.Month.Year"),
        ("%m/%d/%Y", "Month/Date/Year"),
    )
    date_format = models.CharField(max_length=20, choices=DATE_FORMAT_CHOICES)
    FRONT_PAGE_CHOICES = (
        ("BANKING", "Banking"),
        ("ALTERNATIVE", "Alternative"),
        ("CRYPTO", "Crypto"),
        ("SETTINGS", "Settings"),
    )
    front_page = models.CharField(
        max_length=20, choices=FRONT_PAGE_CHOICES, default="SETTINGS"
    )
    rounded_numbers = models.BooleanField(default=True)

    if TYPE_CHECKING:
        crypto_depots: QuerySet[CryptoDepto]
        stock_depots: QuerySet[StockDepot]
        alternative_depots: QuerySet[AlternativeDepot]
        banking_depots: QuerySet[BankingDepot]
        buckets: QuerySet["Bucket"]

    # getters
    def get_active_crypto_depot(self):
        try:
            return self.crypto_depots.get(is_active=True)
        except ObjectDoesNotExist:
            return None
        except MultipleObjectsReturned:
            self.crypto_depots.update(is_active=False)
        return None

    def get_active_stocks_depot(self):
        try:
            return self.stock_depots.get(is_active=True)
        except ObjectDoesNotExist:
            return None
        except MultipleObjectsReturned:
            self.stock_depots.update(is_active=False)
        return None

    def get_active_banking_depot(self):
        try:
            return self.banking_depots.get(is_active=True)
        except ObjectDoesNotExist:
            return None
        except MultipleObjectsReturned:
            self.banking_depots.update(is_active=False)
        return None

    def get_active_alternative_depot(self):
        try:
            return self.alternative_depots.get(is_active=True)
        except ObjectDoesNotExist:
            return None
        except MultipleObjectsReturned:
            self.alternative_depots.update(is_active=False)
        return None

    def get_all_active_depots(
        self,
    ) -> list[Union["BankingDepot", "AlternativeDepot", "CryptoDepto", "StockDepot"]]:
        depots = []
        depot = self.get_active_banking_depot()
        if depot:
            depots.append(depot)
        depot = self.get_active_alternative_depot()
        if depot:
            depots.append(depot)
        depot = self.get_active_crypto_depot()
        if depot:
            depots.append(depot)
        depot = self.get_active_stocks_depot()
        if depot:
            depots.append(depot)
        return depots

    # create
    def create_random_banking_data(self):
        from apps.banking.models import Account, Category, Change, Depot

        name = "Depot {}".format(random.randrange(100, 999))
        depot = Depot.objects.create(name=name, user=self, is_active=True)
        # account
        account1 = Account(depot=depot, name="Bank #1")
        account1.save()
        account2 = Account.objects.create(depot=depot, name="Bank #2")
        account2.save()
        # category
        category1 = Category.objects.create(
            depot=depot,
            name="Category #1",
            description="This category is for test purposes only.",
        )
        category1.save()
        category2 = Category.objects.create(
            depot=depot,
            name="Category #2",
            description="This category is for test purposes only.",
        )
        category2.save()
        category3 = Category.objects.create(
            depot=depot,
            name="Category #3",
            description="This category is for test purposes only.",
        )
        category3.save()
        # changes
        changes = list()
        for i in range(0, 20):
            random_number = random.randint(1, 2)
            account = account1 if random_number == 1 else account2
            random_number = random.randint(1, 3)
            category = (
                category1
                if random_number == 1
                else category2
                if random_number == 2
                else category3
            )
            random_number = random.randint(-400, 600)
            change = random_number
            random_number = random.randint(1, 90)
            date = timezone.now() - timedelta(days=random_number)
            description = "Change #{}".format(i)
            changes.append(
                Change(
                    account=account,
                    category=category,
                    change=change,
                    date=date,
                    description=description,
                )
            )
        Change.objects.bulk_create(changes)
        # return the depot that was created and contains the test data
        return depot

    def create_random_alternative_data(self):
        from datetime import timedelta

        from django.utils import timezone

        from apps.alternative.forms import FlowForm, ValueForm
        from apps.alternative.models import Alternative, Depot

        name = "Depot {}".format(random.randrange(100, 999))
        depot = Depot.objects.create(name=name, user=self, is_active=True)

        # helper create alternative
        def create_alternative(name):
            alternative = Alternative(depot=depot, name=name)
            alternative.save()
            return alternative

        # helper create flow
        def create_flow(alternative, days_before_now, flow_flow):
            date = timezone.now().replace(hour=00, minute=00) - timedelta(
                days=days_before_now, hours=13
            )
            flow = FlowForm(
                depot, {"alternative": alternative.pk, "date": date, "flow": flow_flow}
            )
            flow.save()
            return flow

        # helper create value
        def create_value(alternative, days_before_now, value_value):
            date = timezone.now().replace(hour=00, minute=00) - timedelta(
                days=days_before_now, hours=12
            )
            value = ValueForm(
                depot,
                {"alternative": alternative.pk, "date": date, "value": value_value},
            )
            value.save()
            return value

        # alternatives
        alternative1 = create_alternative("Old-Timer")
        alternative2 = create_alternative("Black-Watch")
        alternative3 = create_alternative("Tube Amplifier")

        # 1
        create_flow(alternative1, 50, 100.0)
        create_value(alternative1, 50, 100.0)
        create_value(alternative1, 30, 110.20)
        create_flow(alternative1, 20, 50.0)
        create_value(alternative1, 20, 160.20)
        create_value(alternative1, 0, 160.20)
        # 2
        create_flow(alternative2, 40, 100.0)
        create_value(alternative2, 40, 100.0)
        create_value(alternative2, 0, 200.50)
        # 3
        create_flow(alternative3, 30, 100.0)
        create_value(alternative3, 30, 100.0)
        create_value(alternative3, 20, 50.1)
        create_flow(alternative3, 10, 10.0)
        create_value(alternative3, 10, 60.0)
        create_value(alternative3, 0, 60.0)

        # return the depot that contains all the test data
        return depot

    def create_random_crypto_data(self):
        from datetime import timedelta

        from django.utils import timezone

        from apps.crypto.forms import FlowForm, TradeForm, TransactionForm
        from apps.crypto.models import Account, Asset, Depot

        # helpers
        def create_trade(
            depot, days_before, account, buy_amount, buy_asset, sell_amount, sell_asset
        ):
            date = timezone.now() - timedelta(days=days_before)
            trade = TradeForm(
                depot,
                {
                    "account": account,
                    "date": date,
                    "buy_amount": buy_amount,
                    "buy_asset": buy_asset,
                    "sell_amount": sell_amount,
                    "sell_asset": sell_asset,
                },
            )
            trade.save()
            return trade

        def create_transaction(
            depot, days_before, amount, fees, asset, from_account, to_account
        ):
            date = timezone.now() - timedelta(days=days_before)
            transaction = TransactionForm(
                depot,
                {
                    "asset": asset,
                    "from_account": from_account,
                    "to_account": to_account,
                    "date": date,
                    "amount": amount,
                    "fees": fees,
                },
            )
            transaction.save()
            return transaction

        def create_flow(depot, days_before, flow, account):
            date = timezone.now() - timedelta(days=days_before)
            flow = FlowForm(depot, {"date": date, "flow": flow, "account": account})
            flow.save()
            return flow

        # depot
        depot = Depot.objects.create(name="Test Depot", user=self, is_active=True)
        # account
        account1 = Account.objects.create(depot=depot, name="Wallet 1")
        account2 = Account.objects.create(depot=depot, name="Exchange 1")
        # asset
        btc = Asset.objects.create(depot=depot, symbol="BTC")
        eth = Asset.objects.create(depot=depot, symbol="ETH")
        ltc = Asset.objects.create(depot=depot, symbol="LTC")
        eur = Asset.objects.get(depot=depot, symbol="EUR")
        # flow
        create_flow(depot, 60, 6000, account1)
        create_flow(depot, 55, 2000, account2)
        # trade
        create_trade(depot, 50, account1, 1, btc, 5000, eur)
        create_trade(depot, 50, account2, 10, eth, 2000, eur)
        create_trade(depot, 30, account2, 15, ltc, 5, eth)
        # transaction
        create_transaction(depot, 20, 5, 1, ltc, account2, account1)
        # return the depot with the generated data
        return depot

    def create_random_stocks_data(self):
        from apps.stocks.forms import FlowForm, TradeForm
        from apps.stocks.models import Bank, Depot, Stock

        # helpers
        def create_trade(
            depot, date, bank, money_amount, stock_amount, stock, buy_or_sell
        ):
            trade = TradeForm(
                depot,
                {
                    "bank": bank,
                    "date": date,
                    "money_amount": money_amount,
                    "stock_amount": stock_amount,
                    "stock": stock,
                    "buy_or_sell": buy_or_sell,
                },
            )
            trade = trade.save()
            return trade

        def create_flow(depot, date, flow, bank):
            flow = FlowForm(depot, {"date": date, "flow": flow, "bank": bank})
            flow = flow.save()
            return flow

        # depot
        name = "Depot {}".format(random.randrange(100, 999))
        depot = Depot.objects.create(name=name, user=self, is_active=True)
        # bank
        bank = Bank.objects.create(name="Big Bank", depot=depot)
        # stock
        stock = Stock.objects.create(
            depot=depot, name="Varta AG", ticker="VAR1", exchange="XETRA"
        )
        # flow
        create_flow(depot, "2020-03-03T13:45", 10000, bank)
        # trade
        create_trade(depot, "2020-07-22T09:22", bank, 10000, 100, stock, "BUY")
        # return
        return depot
