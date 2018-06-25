from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test import Client

from finance.crypto.models import init_crypto
from finance.crypto.models import Account
from finance.crypto.models import Depot
from finance.crypto.forms import CreateTimespanForm
from finance.crypto.forms import CreateAccountForm
from finance.crypto.forms import CreateDepotForm
from finance.users.models import StandardUser


# Create your tests here.
class ViewsTestCase(TestCase):
    def setUp(self):
        user = StandardUser.objects.create_user(username="Dummy")
        user.set_password("test")
        user.save()
        init_crypto(user)

    def test_index_view(self):
        client = Client()
        client.login(username="Dummy", password="test")
        user = StandardUser.objects.get(username="Dummy")
        response = client.get(reverse("crypto:index", args=[user.slug, ]))
        self.assertEqual(response.status_code, 200)

    def test_account_view(self):
        client = Client()
        client.login(username="Dummy", password="test")
        user = StandardUser.objects.get(username="Dummy")
        account = user.banking_depots.get(is_active=True).accounts.first()
        response = client.get(reverse("crypto:account", args=[user.slug, account.slug]))
        self.assertEqual(response.status_code, 200)

    def test_category_view(self):
        client = Client()
        client.login(username="Dummy", password="test")
        user = StandardUser.objects.get(username="Dummy")
        category = user.banking_depots.get(is_active=True).categories.first()
        response = client.get(reverse("crypto:asset", args=[user.slug, category.slug]))
        self.assertEqual(response.status_code, 200)