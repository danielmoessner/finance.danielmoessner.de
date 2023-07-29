from datetime import timedelta

from django.test import Client, TestCase
from django.urls import reverse_lazy
from django.utils import timezone

from apps.banking.forms import AccountForm, CategoryForm, ChangeForm, DepotForm
from apps.banking.models import Account, Category, Change, Depot
from apps.users.models import StandardUser as User


def create_account(depot, name=None):
    form = AccountForm(depot, {"name": name})
    assert form.is_valid()
    return form.save()


def create_category(depot, name=None, description=""):
    form = CategoryForm(depot, {"name": name, "description": description})
    assert form.is_valid()
    return form.save()


def create_depot(user, name=None):
    form = DepotForm(user, {"name": name})
    assert form.is_valid()
    return form.save()


def create_change(
    depot, account=None, category=None, date=None, change=10, description=""
):
    form = ChangeForm(
        depot,
        {
            "account": account,
            "category": category,
            "date": date,
            "change": change,
            "description": description,
        },
    )
    assert form.is_valid()
    return form.save()


class ViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dummy")
        self.user.set_password("test")
        self.user.save()
        self.user.create_random_banking_data()

    def test_index_view(self):
        self.client = Client()
        self.client.login(username="dummy", password="test")
        self.user = User.objects.get(username="dummy")
        response = self.client.get(reverse_lazy("banking:index", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            "{}?tab=stats".format(reverse_lazy("banking:index", args=[1]))
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            "{}?tab=categories".format(reverse_lazy("banking:index", args=[1]))
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            "{}?tab=accounts".format(reverse_lazy("banking:index", args=[1]))
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            "{}?tab=charts".format(reverse_lazy("banking:index", args=[1]))
        )
        self.assertEqual(response.status_code, 200)

    def test_account_view(self):
        self.client = Client()
        self.client.login(username="dummy", password="test")
        self.user = User.objects.get(username="dummy")
        account = self.user.banking_depots.get(is_active=True).accounts.first()
        url = reverse_lazy("banking:account", args=[account.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get("{}?tab=stats".format(url))
        self.assertEqual(response.status_code, 200)
        response = self.client.get("{}?tab=changes".format(url))
        self.assertEqual(response.status_code, 200)

    def test_category_view(self):
        self.client = Client()
        self.client.login(username="dummy", password="test")
        self.user = User.objects.get(username="dummy")
        category = self.user.banking_depots.get(is_active=True).categories.first()
        url = reverse_lazy("banking:category", args=[category.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get("{}?tab=stats".format(url))
        self.assertEqual(response.status_code, 200)
        response = self.client.get("{}?tab=changes".format(url))
        self.assertEqual(response.status_code, 200)


class BalanceUpdateTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dummy")
        self.user.set_password("test")
        self.user.save()
        self.depot_pk = create_depot(self.user, "Depot").pk
        self.account_pk = create_account(self.get_depot(), "Account").pk
        self.category_pk = create_category(self.get_depot(), "Category").pk

    def get_account(self):
        return Account.objects.get(pk=self.account_pk)

    def get_category(self):
        return Category.objects.get(pk=self.category_pk)

    def get_depot(self):
        return Depot.objects.get(pk=self.depot_pk)

    def create_change_and_set_balances(self, days_ago=20):
        date_x_days_ago = timezone.now() - timedelta(days=days_ago)
        change = create_change(
            self.get_depot(),
            account=self.get_account(),
            category=self.get_category(),
            date=date_x_days_ago,
        )
        # set the balances
        self.get_account().get_stats()
        self.get_depot().get_stats()
        self.get_category().get_stats()
        # return the change
        return change

    def test_balance_is_set_properly(self):
        self.create_change_and_set_balances()
        # test that stats are being set properly
        assert self.get_account().balance is not None
        assert self.get_depot().balance is not None
        assert self.get_category().balance is not None

    def test_balance_is_reset_properly_after_change_added(self):
        self.create_change_and_set_balances(days_ago=20)
        # test that balances are reset properly after a change is added
        days_ago_10 = timezone.now() - timedelta(days=10)
        create_change(
            self.get_depot(),
            account=self.get_account(),
            category=self.get_category(),
            date=days_ago_10,
        )
        assert self.get_account().balance is None
        assert self.get_category().balance is None
        assert self.get_depot().balance is None

    def test_balance_is_reset_after_change_deletion(self):
        change1 = self.create_change_and_set_balances(days_ago=20)
        change2 = self.create_change_and_set_balances(days_ago=10)
        # test that balances are reset properly after a change is added
        change1.delete()
        assert Change.objects.get(pk=change2.pk).balance is None
        assert self.get_account().balance is None
        assert self.get_category().balance is None
        assert self.get_depot().balance is None

    def test_balance_is_not_set_to_none_after_no_changes(self):
        change = self.create_change_and_set_balances()
        # test that balances are not resetted
        change.save()
        assert self.get_account().balance is not None
        assert self.get_category().balance is not None
        assert self.get_depot().balance is not None
