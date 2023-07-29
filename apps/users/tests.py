from django.test import Client, TestCase
from django.urls import reverse_lazy

from apps.users.models import StandardUser as User


class ViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dummy")
        self.user.set_password("test")
        self.user.save()
        self.user.create_random_banking_data()

    def test_login_view(self):
        self.client = Client()
        response = self.client.get(reverse_lazy("users:signin"))
        self.assertEqual(response.status_code, 200)

    def test_signup_view(self):
        self.client = Client()
        response = self.client.get(reverse_lazy("users:signup"))
        self.assertEqual(response.status_code, 200)

    def test_index_view(self):
        self.client = Client()
        self.client.login(username="dummy", password="test")
        response = self.client.get(reverse_lazy("users:settings", args=[self.user.pk]))
        self.assertEqual(response.status_code, 200)
        url = "{}?tab=banking".format(
            reverse_lazy("users:settings", args=[self.user.pk])
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            "{}?tab=alternative".format(
                reverse_lazy("users:settings", args=[self.user.pk])
            )
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            "{}?tab=crypto".format(reverse_lazy("users:settings", args=[self.user.pk]))
        )
        self.assertEqual(response.status_code, 200)

    def test_init_works(self):
        self.client = Client()
        self.client.login(username="dummy", password="test")
        response = self.client.get(
            reverse_lazy("users:init_banking", args=[self.user.pk])
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse_lazy("users:init_alternative", args=[self.user.pk])
        )
        self.assertEqual(response.status_code, 302)
