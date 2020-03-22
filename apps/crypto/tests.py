from django.urls import reverse_lazy
from django.test import TestCase
from django.test import Client

from apps.crypto.models import init_crypto
from apps.crypto.models import Asset
from apps.users.models import StandardUser


class ViewsTestCase(TestCase):
    def setUp(self):
        user = StandardUser.objects.create_user(username="Dummy")
        user.set_password("test")
        user.save()
        Asset.objects.create(symbol="BTC", slug="bitcoin")
        Asset.objects.create(symbol="ETH", slug="ethereum")
        Asset.objects.create(symbol="LTC", slug="litecoin")
        Asset.objects.create(symbol="EUR", slug="euro")
        init_crypto(user)

    def test_index_view(self):
        client = Client()
        client.login(username="Dummy", password="test")
        user = StandardUser.objects.get(username="Dummy")
        response = client.get(reverse_lazy("crypto:index"))
        self.assertEqual(response.status_code, 200)

    def test_account_view(self):
        client = Client()
        client.login(username="Dummy", password="test")
        user = StandardUser.objects.get(username="Dummy")
        account = user.crypto_depots.get(is_active=True).accounts.first()
        response = client.get(reverse_lazy("crypto:account", args=[account.slug]))
        self.assertEqual(response.status_code, 200)

    def test_asset_view(self):
        client = Client()
        client.login(username="Dummy", password="test")
        user = StandardUser.objects.get(username="Dummy")
        asset = user.crypto_depots.get(is_active=True).assets.first()
        response = client.get(reverse_lazy("crypto:asset", args=[asset.slug]))
        self.assertEqual(response.status_code, 200)
