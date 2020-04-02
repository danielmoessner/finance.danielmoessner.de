from django.utils import timezone
from django.urls import reverse_lazy
from django.test import TestCase
from django.test import Client

from apps.crypto.models import Asset, Depot, Account
from apps.users.models import StandardUser
from apps.crypto.forms import DepotForm, FlowForm, TransactionForm, TradeForm

from datetime import timedelta


class ViewsTestCase(TestCase):
    def setUp(self):
        self.user = StandardUser.objects.create_user(username="Dummy2")
        self.user.set_password("test")
        self.user.save()
        self.client = Client()
        self.client.login(username="Dummy2", password="test")
        self.depot = self.user.create_random_crypto_data()

    def test_index_view(self):
        url = reverse_lazy("crypto:index", args=[self.depot.pk])
        for tab in ['', 'stats', 'assets', 'accounts', 'trades', 'transactions', 'flows', 'charts']:
            response = self.client.get('{}?tab={}'.format(url, tab))
            self.assertEqual(response.status_code, 200)

    def test_account_view(self):
        url = reverse_lazy("crypto:account", args=[self.depot.accounts.first().pk])
        for tab in ['', 'stats', 'assets', 'trades', 'transactions', 'flows']:
            response = self.client.get('{}?tab={}'.format(url, tab))
            self.assertEqual(response.status_code, 200)

    def test_asset_view(self):
        url = reverse_lazy("crypto:asset", args=[self.depot.assets.first().pk])
        for tab in ['', 'stats', 'prices', 'trades', 'transactions']:
            response = self.client.get('{}?tab={}'.format(url, tab))
            self.assertEqual(response.status_code, 200)


class FormValidationTestCase(TestCase):
    def setUp(self):
        self.user = StandardUser.objects.create_user(username="Dummy")
        self.user.set_password("test")
        self.user.save()
        self.client = Client()
        self.client.login(username="Dummy", password="test")
        self.depot = self.user.create_random_crypto_data()
        self.account = Account.objects.create(depot=self.depot, name='Test Acc')

    def create_trade(self, days_before, account, buy_amount, buy_asset, sell_amount, sell_asset, date=None):
        date = timezone.now() - timedelta(days=days_before) if date is None else date
        trade = TradeForm(self.depot, {'account': account, 'date': date, 'buy_amount': buy_amount,
                                       'buy_asset': buy_asset, 'sell_amount': sell_amount, 'sell_asset': sell_asset})
        trade = trade.save()
        return trade

    def create_transaction(self, days_before, amount, fees, asset, from_account, to_account, date=None):
        date = timezone.now() - timedelta(days=days_before) if date is None else date
        transaction = TransactionForm(self.depot, {'asset': asset, 'from_account': from_account,
                                                   'to_account': to_account, 'date': date, 'amount': amount,
                                                   'fees': fees})
        transaction = transaction.save()
        return transaction

    def create_flow(self, days_before, flow, account, date=None):
        date = timezone.now() - timedelta(days=days_before) if date is None else date
        flow = FlowForm(self.depot, {'date': date, 'flow': flow, 'account': account})
        flow = flow.save()
        return flow

    def test_flow_form_not_allowing_more_withdraw_than_possible(self):
        # test you can not withdraw if there is no asset
        with self.assertRaises(ValueError):
            self.create_flow(30, -1000, self.account)
        # test you can not withdraw if there is not enough asset
        self.create_flow(20, 1000, self.account)
        with self.assertRaises(ValueError):
            self.create_flow(10, -2000, self.account)
        # test you can not withdraw earlier than the asset was added
        with self.assertRaises(ValueError):
            self.create_flow(25, -500, self.account)
        # test you can actually withdraw all of the asset that is there
        self.create_flow(10, -1000, self.account)

    def test_trade_form_allowing_amount_change(self):
        flow = self.create_flow(20, 1000, self.account)
        btc, created = self.depot.assets.get_or_create(symbol='BTC')
        eur = self.depot.assets.get(symbol='EUR')
        trade = self.create_trade(10, self.account, 1, btc, 900, eur)
        trade_new = TradeForm(self.depot, instance=trade,
                              data={'account': trade.account, 'date': trade.date, 'buy_amount': trade.buy_amount,
                                    'buy_asset': trade.buy_asset, 'sell_amount': 950,
                                    'sell_asset': trade.sell_asset})
        trade_new.save()

    def test_flow_form_allowing_amount_change(self):
        flow = self.create_flow(20, 1000, self.account)
        flow = self.create_flow(10, -1000, self.account)
        flow_new = FlowForm(self.depot, instance=flow, data={'date': flow.date, 'flow': -500, 'account': flow.account})
        flow_new.save()

    def test_transaction_form_allowing_amount_change(self):
        eur = self.depot.assets.get(symbol='EUR')
        flow = self.create_flow(20, 1000, self.account)
        account2 = Account.objects.create(depot=self.depot, name='acc2')
        transaction = self.create_transaction(10, 900, 10, eur, self.account, account2)
        transaction_new = TransactionForm(self.depot, instance=transaction,
                                          data={'asset': transaction.asset, 'from_account': transaction.from_account,
                                                'to_account': transaction.to_account, 'date': transaction.date,
                                                'amount': 950,
                                                'fees': transaction.fees})
        transaction_new.save()

    def test_no_trade_transaction_or_flow_on_the_same_account_and_date(self):
        flow = self.create_flow(10, 1000, self.account)
        btc, created = self.depot.assets.get_or_create(symbol='BTC')
        eur = self.depot.assets.get(symbol='EUR')
        account2 = Account.objects.create(depot=self.depot, name='acc2')
        flow = self.create_flow(10, 1000, account2)
        # test
        date = timezone.now()
        # test with existing flow
        flow = self.create_flow(0, 1000, self.account, date=date)
        with self.assertRaises(ValueError):
            self.create_transaction(0, 500, 10, eur, self.account, account2, date=date)
        with self.assertRaises(ValueError):
            self.create_transaction(0, 500, 10, eur, account2, self.account, date=date)
        with self.assertRaises(ValueError):
            self.create_trade(0, self.account, 1, btc, 500, eur, date=date)
        flow.delete()
        # test with existing trade
        trade = self.create_trade(0, self.account, 1, btc, 500, eur, date=date)
        with self.assertRaises(ValueError):
            self.create_transaction(0, 500, 10, eur, self.account, account2, date=date)
        with self.assertRaises(ValueError):
            self.create_transaction(0, 500, 10, eur, self.account, account2, date=date)
        with self.assertRaises(ValueError):
            flow = self.create_flow(0, 1000, self.account, date=date)
        trade.delete()
        # test with existing transaction
        self.create_transaction(0, 500, 10, eur, self.account, account2, date=date)
        with self.assertRaises(ValueError):
            flow = self.create_flow(0, 1000, self.account, date=date)
        with self.assertRaises(ValueError):
            flow = self.create_flow(0, 1000, account2, date=date)
        with self.assertRaises(ValueError):
            self.create_trade(0, self.account, 1, btc, 500, eur, date=date)
        with self.assertRaises(ValueError):
            self.create_trade(0, account2, 1, btc, 500, eur, date=date)

    def test_trade_form_not_allowing_more_sell_asset_than_what_is_available(self):
        self.create_flow(20, 1000, self.account)
        btc, created = self.depot.assets.get_or_create(symbol='BTC')
        eur = self.depot.assets.get(symbol='EUR')
        # test you can not sell asset that you don't have
        with self.assertRaises(ValueError):
            self.create_trade(19, self.account, 1, btc, 1100, eur)
        # test you can not sell an asset before it actualy arrived at your account
        with self.assertRaises(ValueError):
            self.create_trade(30, self.account, 1, btc, 500, eur)
        # test you can actually sell an asset
        self.create_trade(10, self.account, 1, btc, 1000, eur)

    def test_transaction_form_not_allowing_to_send_more_than_available(self):
        self.create_flow(20, 1000, self.account)
        eur = self.depot.assets.get(symbol='EUR')
        account2 = Account.objects.create(depot=self.depot, name='acc2')
        # test you can't send more than available
        with self.assertRaises(ValueError):
            self.create_transaction(10, 1000, 10, eur, self.account, account2)
        # test you can not send before the asset arrived
        with self.assertRaises(ValueError):
            self.create_transaction(30, 500, 10, eur, self.account, account2)
        # test you can actually send assets
        self.create_transaction(10, 990, 10, eur, self.account, account2)
