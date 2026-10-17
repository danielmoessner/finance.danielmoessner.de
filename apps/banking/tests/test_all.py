from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse_lazy
from django.utils import timezone

from apps.banking.forms import (
    AccountForm,
    CategoryForm,
    ChangeForm,
    CsvImportForm,
    DepotForm,
)
from apps.banking.models import (
    Account,
    Category,
    Change,
    ComdirectImport,
    ComdirectImportChange,
    CsvImport,
    Depot,
)
from apps.core.functional import list_sort
from apps.users.models import StandardUser as User


def create_account(depot, name=None):
    form = AccountForm(depot, {"name": name, "default_date": "today"})
    assert form.is_valid(), form.errors
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
        self.user = User.objects.create_user(username="dummy")  # type: ignore
        self.user.set_password("test")
        self.user.save()
        self.user.create_random_banking_data()

    def test_index_view(self):
        self.client = Client()
        self.client.login(username="dummy", password="test")
        self.user = User.objects.get(username="dummy")
        response = self.client.get(reverse_lazy("banking:index"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get("{}?tab=stats".format(reverse_lazy("banking:index")))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            "{}?tab=categories".format(reverse_lazy("banking:index"))
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            "{}?tab=accounts".format(reverse_lazy("banking:index"))
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            "{}?tab=charts".format(reverse_lazy("banking:index"))
        )
        self.assertEqual(response.status_code, 200)
        depot = self.user.banking_depots.get(is_active=True)
        self.assertEqual(
            set(response.context["accounts"].values_list("pk", flat=True)),
            set(depot.accounts.values_list("pk", flat=True)),
        )
        self.assertEqual(
            set(response.context["categories"].values_list("pk", flat=True)),
            set(depot.categories.values_list("pk", flat=True)),
        )

    def test_budget_view_shows_average_over_the_12_months(self):
        self.client = Client()
        self.client.login(username="dummy", password="test")
        depot = self.user.banking_depots.get(is_active=True)
        account = depot.accounts.first()
        assert account is not None
        category = create_category(depot, name="Budget average")
        category.monthly_budget = Decimal("100")
        category.save()

        current_month = timezone.localdate().replace(day=1)
        previous_month = (current_month - timedelta(days=1)).replace(day=1)
        for month, amount in (
            (current_month, Decimal("-120")),
            (previous_month, Decimal("-60")),
        ):
            Change.objects.create(
                account=account,
                category=category,
                date=timezone.make_aware(
                    datetime.combine(month, datetime.min.time()),
                    timezone.get_current_timezone(),
                ),
                change=amount,
            )

        response = self.client.get(
            "{}?tab=budgets".format(reverse_lazy("banking:index"))
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["category_averages"][category.pk], "15,00 €")
        html = response.content.decode()
        self.assertIn("15,00 €", html)
        self.assertLess(html.index(">Available<"), html.index(">Avg<"))

    def test_income_and_expenditure_data_uses_local_month(self):
        depot = self.user.banking_depots.get(is_active=True)
        account = depot.accounts.first()
        assert account is not None
        category = create_category(depot, name="Timezone boundary expense")
        month_start = timezone.localdate().replace(day=1)
        local_midnight = timezone.make_aware(
            datetime.combine(month_start, datetime.min.time()),
            timezone.get_current_timezone(),
        )
        Change.objects.create(
            account=account,
            category=category,
            date=local_midnight,
            change=Decimal("-123.45"),
        )

        data = depot.get_income_and_expenditure_data()
        rows_for_category = [row for row in data if category.name in row]

        self.assertEqual(len(rows_for_category), 1)
        self.assertEqual(rows_for_category[0]["date"], month_start.strftime("%Y-%m"))
        self.assertEqual(rows_for_category[0][category.name], -123.45)
        self.assertEqual(category.get_month_amount(month_start), Decimal("123.45"))

    def test_statements_use_local_month_for_changes(self):
        depot = self.user.banking_depots.get(is_active=True)
        account = depot.accounts.first()
        assert account is not None
        category = create_category(depot, name="Statements timezone boundary")
        month_start = timezone.localdate().replace(day=1)
        Change.objects.create(
            account=account,
            category=category,
            date=timezone.make_aware(
                datetime.combine(month_start, datetime.min.time()),
                timezone.get_current_timezone(),
            ),
            change=Decimal("-123.45"),
        )

        statements = depot.get_statements()

        month_label = month_start.strftime("%B %y")
        month_index = statements["months"].index(month_label)
        self.assertEqual(
            statements["data"][category.name][month_index],
            -123.45,
        )

    def test_account_view(self):
        self.client = Client()
        self.client.login(username="dummy", password="test")
        self.user = User.objects.get(username="dummy")
        depot = self.user.banking_depots.get(is_active=True)
        assert depot is not None
        account = depot.accounts.first()
        assert account is not None
        url = reverse_lazy("banking:account", args=[account.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get("{}?tab=stats".format(url))
        self.assertEqual(response.status_code, 200)
        response = self.client.get("{}?tab=changes".format(url))
        self.assertEqual(response.status_code, 200)

    def test_import_preview_does_not_show_midnight_for_date_only_transactions(self):
        self.client = Client()
        self.client.force_login(self.user)
        account = self.user.banking_depots.get(is_active=True).accounts.first()
        assert account is not None
        comdirect_import = ComdirectImport.objects.create(
            account=account,
            comdirect_api_client_id="client-id",
            comdirect_api_client_secret="client-secret",
            comdirect_zugangsnummer="access-number",
            comdirect_pin="pin",
            comdirect_account_id="account-id",
        )
        ComdirectImportChange.objects.create(
            comdirect_import=comdirect_import,
            sha="test-sha",
            date=date(2001, 1, 2),
            description="Imported transaction",
            change=Decimal("-12.34"),
        )

        response = self.client.get(
            f"{reverse_lazy('banking:account', args=[account.pk])}?tab=import"
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "02.01.2001")
        self.assertNotContains(response, "02.01.2001 00:00")

    def test_category_view(self):
        self.client = Client()
        self.client.login(username="dummy", password="test")
        self.user = User.objects.get(username="dummy")
        depot = self.user.banking_depots.get(is_active=True)
        assert depot is not None
        category = depot.categories.first()
        assert category is not None
        url = reverse_lazy("banking:category", args=[category.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get("{}?tab=stats".format(url))
        self.assertEqual(response.status_code, 200)
        response = self.client.get("{}?tab=changes".format(url))
        self.assertEqual(response.status_code, 200)


class BalanceUpdateTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dummy")  # type: ignore
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

    def test_comdirect_import_uses_local_noon(self):
        transaction_date = timezone.localdate()
        imported_change = ComdirectImportChange(
            comdirect_import=ComdirectImport(account=self.get_account()),
            date=transaction_date,
            description="Imported transaction",
            change=Decimal("-12.34"),
        )

        change = imported_change.import_into_account(self.get_category())
        change.save()
        persisted_change = Change.objects.get(pk=change.pk)

        self.assertEqual(
            timezone.localtime(persisted_change.date).hour,
            12,
        )
        self.assertEqual(
            timezone.localtime(persisted_change.date).date(), transaction_date
        )

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

    def test_balance_is_reset_after_change_deletion(self):
        change1 = self.create_change_and_set_balances(days_ago=20)
        change2 = self.create_change_and_set_balances(days_ago=10)
        # test that balances are reset properly after a change is added
        change1.delete()
        assert Change.objects.get(pk=change2.pk).balance is None
        assert self.get_account().balance is None
        assert self.get_category().balance is None

    def test_balance_is_not_set_to_none_after_no_changes(self):
        change = self.create_change_and_set_balances()
        # test that balances are not resetted
        change.save()
        assert self.get_account().balance is not None
        assert self.get_category().balance is not None
        assert self.get_depot().balance is not None

    def test_csv_import_resets_cached_balances(self):
        self.create_change_and_set_balances(days_ago=20)
        assert self.get_depot().balance is not None

        csv_content = (
            "Datum,Kategorie,Beschreibung,Cashflow\n"
            "01.01.2026,Imported Category,CSV Import,-20 €\n"
        )
        upload = SimpleUploadedFile(
            "import.csv",
            csv_content.encode("utf-8"),
            content_type="text/csv",
        )
        form = CsvImportForm(
            self.get_depot(),
            data={"map": '{"Imported Category":"Category"}'},
            files={"file": upload},
            instance=CsvImport(account=self.get_account(), map={}),
        )
        assert form.is_valid(), form.errors
        form.save()

        assert self.get_depot().balance is None
        assert self.get_account().balance is None
        assert self.get_category().balance is None

    def test_category_sort(self):
        a = {"n": "a", "s": [1, 2, 3]}
        b = {"n": "b", "s": [2, 3, 4]}
        c = {"n": "c", "s": [0, 0, 5]}
        d = {"n": "d", "s": [-4, -5, -6]}
        e = {"n": "e", "s": [-4, 1, 2]}
        res = list_sort([a, b, c, d, e], lambda x: x["s"], reverse=True)
        assert res == [b, a, c, e, d]
