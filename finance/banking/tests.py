from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test import Client

from finance.banking.models import init_banking
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
        response = client.get(reverse("banking:index"))
        self.assertEqual(response.status_code, 200)

    def test_account_view(self):
        client = Client()
        client.login(username="Dummy", password="test")
        user = StandardUser.objects.get(username="Dummy")
        account = user.banking_depots.get(is_active=True).accounts.first()
        response = client.get(reverse("banking:account", args=[account.slug]))
        self.assertEqual(response.status_code, 200)

    def test_category_view(self):
        client = Client()
        client.login(username="Dummy", password="test")
        user = StandardUser.objects.get(username="Dummy")
        category = user.banking_depots.get(is_active=True).categories.first()
        response = client.get(reverse("banking:category", args=[category.slug]))
        self.assertEqual(response.status_code, 200)
