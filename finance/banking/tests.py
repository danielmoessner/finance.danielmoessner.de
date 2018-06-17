from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test import Client

from finance.banking.models import init_banking
from finance.banking.models import Category
from finance.banking.models import Account
from finance.banking.models import Depot
from finance.banking.forms import CreateCategoryForm
from finance.banking.forms import CreateTimespanForm
from finance.banking.forms import CreateAccountForm
from finance.banking.forms import CreateChangeForm
from finance.banking.forms import CreateDepotForm
from finance.users.models import StandardUser


class ViewsTestCase(TestCase):
    def setUp(self):
        user = StandardUser.objects.create_user(username="Dummy")
        user.set_password("test")
        user.save()
        init_banking(user)

    def test_index_view(self):
        client = Client()
        client.login(username="Dummy", password="test")
        user = StandardUser.objects.get(username="Dummy")
        response = client.get(reverse("banking:index", args=[user.slug, ]))
        self.assertEqual(response.status_code, 200)

    def test_account_view(self):
        client = Client()
        client.login(username="Dummy", password="test")
        user = StandardUser.objects.get(username="Dummy")
        account = user.banking_depots.get(is_active=True).accounts.first()
        response = client.get(reverse("banking:account", args=[user.slug, account.slug]))
        self.assertEqual(response.status_code, 200)

    def test_category_view(self):
        client = Client()
        client.login(username="Dummy", password="test")
        user = StandardUser.objects.get(username="Dummy")
        category = user.banking_depots.get(is_active=True).categories.first()
        response = client.get(reverse("banking:category", args=[user.slug, category.slug]))
        self.assertEqual(response.status_code, 200)


class FormsTestCase(TestCase):
    def setUp(self):
        user = StandardUser.objects.create_user(username="dummyuser")
        user.set_password("test")
        user.save()
        depot = Depot.objects.create(user=user, name="dummydepot")
        depot.save()
        account = Account.objects.create(depot=depot, name="dummyaccount")
        account.save()
        category = Category.objects.create(depot=depot, name="dummycategory", description="")
        category.save()

    def test_create_depot_form(self):
        form_data = {"name": "depotname"}
        form = CreateDepotForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_create_account_form(self):
        form_data = {"name": "accountname"}
        form = CreateAccountForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_create_category_form(self):
        form_data = {"name": "categoryname", "description": "categorydescription"}
        form = CreateCategoryForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_create_change_form(self):
        form_data = {
            "account": Account.objects.get(name="dummyaccount").pk,
            "date": "2018-06-01T12:00",
            "category": Category.objects.get(name="dummycategory").pk,
            "description": "changedescription",
            "change": "123124.12"
        }
        form = CreateChangeForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_create_timespan_form(self):
        form_data = {
            "name": "timespanname",
            "start_date": "2018-06-01T12:00",
            "end_date": "2018-06-14T12:00"
        }
        form = CreateTimespanForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
