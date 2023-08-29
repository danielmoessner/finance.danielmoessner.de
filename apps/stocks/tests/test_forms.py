from django.test import Client, TestCase

from apps.stocks.forms import FlowForm, TradeForm
from apps.stocks.models import Bank, Depot, Stock
from apps.users.models import StandardUser


class StandardSetUpTestCase(TestCase):
    def setUp(self):
        self.user = StandardUser.objects.create_user(username="Dummy")
        self.user.set_password("test")
        self.user.save()
        self.client = Client()
        self.client.login(username="Dummy", password="test")
        self.depot = self.user.create_random_stocks_data()

    def get_depot(self):
        return Depot.objects.get(pk=self.depot.pk)

    def create_trade(self, date, bank, money_amount, stock_amount, stock, buy_or_sell):
        trade = TradeForm(
            self.depot,
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

    def create_flow(self, date, flow, bank):
        flow = FlowForm(self.depot, {"date": date, "flow": flow, "bank": bank})
        flow = flow.save()
        return flow


class FormValidationTestCase(StandardSetUpTestCase):
    def setUp(self):
        super().setUp()
        self.bank = Bank.objects.create(depot=self.depot, name="Test Bank")
        self.stock = Stock.objects.create(
            name="Test Stock", exchange="TEST", ticker="TST", depot=self.depot
        )

    def test_no_negative_flow_can_be_added_when_balance_zero(self):
        with self.assertRaises(ValueError):
            self.create_flow("2020-05-05T12:40", -1, self.bank)

    def test_negative_flow_can_be_added_when_balance_is_sufficient(self):
        self.create_flow("2020-05-05T12:40", 1, self.bank)
        self.create_flow("2020-05-05T12:41", -1, self.bank)

    def test_flows_can_not_be_on_the_same_date(self):
        self.create_flow("2020-05-05T12:40", 1, self.bank)
        with self.assertRaises(ValueError):
            self.create_flow("2020-05-05T12:40", 1, self.bank)

    def test_buy_trade_can_not_be_added_when_balance_zero(self):
        with self.assertRaises(ValueError):
            self.create_trade("2020-05-05T23:23", self.bank, 1, 1, self.stock, "BUY")

    def test_trade_amounts_can_not_be_negative(self):
        self.create_flow("2020-05-05T12:40", 1, self.bank)
        with self.assertRaises(ValueError):
            self.create_trade("2020-05-05T23:23", self.bank, -1, 1, self.stock, "BUY")
        with self.assertRaises(ValueError):
            self.create_trade("2020-05-05T23:23", self.bank, 1, -1, self.stock, "BUY")

    def test_trade_can_not_be_before_flow_when_balance_is_not_sufficient(self):
        self.create_flow("2020-05-05T12:40", 1, self.bank)
        with self.assertRaises(ValueError):
            self.create_trade("2020-05-04T23:23", self.bank, 1, 1, self.stock, "BUY")

    def test_trade_can_not_be_inserted_before_another_trade_which_turns_balance_negative(  # noqa: E501
        self,
    ):
        self.create_flow("2020-05-05T12:40", 1, self.bank)
        self.create_trade("2020-05-07T12:23", self.bank, 1, 1, self.stock, "BUY")
        with self.assertRaises(ValueError):
            self.create_trade("2020-05-06T14:23", self.bank, 1, 1, self.stock, "BUY")

    def test_trade_can_not_be_inserted_before_trade_with_enough_balance_after_certain_amount_of_time(  # noqa: E501
        self,
    ):
        self.create_flow("2020-05-05T12:40", 1, self.bank)
        self.create_trade("2020-05-07T12:23", self.bank, 1, 1, self.stock, "BUY")
        self.create_flow("2020-05-08T12:40", 1, self.bank)
        with self.assertRaises(ValueError):
            self.create_trade("2020-05-06T12:23", self.bank, 1, 1, self.stock, "BUY")

    def test_flow_can_not_be_inserted_before_flow_and_turn_balance_negative(self):
        self.create_flow("2020-05-05T12:40", 1, self.bank)
        self.create_flow("2020-05-07T12:40", -1, self.bank)
        self.create_flow("2020-05-09T12:40", 1, self.bank)
        with self.assertRaises(ValueError):
            self.create_flow("2020-05-06T12:40", -1, self.bank)
