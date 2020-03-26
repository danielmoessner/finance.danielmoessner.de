from django.utils import timezone
from django.test import TestCase, Client
from django.urls import reverse_lazy

from apps.users.models import StandardUser as User
from .models import Alternative, Depot
from .forms import ValueForm, FlowForm

from datetime import timedelta


class ViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dummy")
        self.user.set_password("test")
        self.user.save()
        self.user.create_random_alternative_data()

    def test_index_view(self):
        self.client = Client()
        self.client.login(username="dummy", password="test")
        url = reverse_lazy("alternative:index", args=[1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get('{}?tab=stats'.format(url))
        self.assertEqual(response.status_code, 200)
        response = self.client.get('{}?tab=alternatives'.format(url))
        self.assertEqual(response.status_code, 200)
        response = self.client.get('{}?tab=calculated'.format(url))
        self.assertEqual(response.status_code, 200)

    def test_account_view(self):
        self.client = Client()
        self.client.login(username="dummy", password="test")
        alternative = self.user.alternative_depots.get(is_active=True).alternatives.first()
        url = reverse_lazy("alternative:alternative", args=[alternative.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get('{}?tab=stats'.format(url))
        self.assertEqual(response.status_code, 200)
        response = self.client.get('{}?tab=data'.format(url))
        self.assertEqual(response.status_code, 200)
        response = self.client.get('{}?tab=calculated'.format(url))
        self.assertEqual(response.status_code, 200)


class GeneralTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dummy")
        self.user.set_password("test")
        self.user.save()
        self.depot = Depot.objects.create(name="Test Depot", user=self.user)
        self.alternative = Alternative.objects.create(depot=self.depot, name="Test Alternative")

    def create_flow(self, days_before_now, flow_flow, hours_before_now=20):
        date = (timezone.now().replace(hour=00, minute=00) - timedelta(days=days_before_now, hours=hours_before_now))
        flow = FlowForm(self.depot, {"alternative": self.alternative.pk, "date": date, "flow": flow_flow})
        flow.save()
        return flow

    def create_value(self, days_before_now, value_value, hours_before_now=4):
        date = (timezone.now().replace(hour=00, minute=00) - timedelta(days=days_before_now, hours=hours_before_now))
        value = ValueForm(self.depot, {"alternative": self.alternative.pk, "date": date, "value": value_value})
        value.save()
        return value

    def test_everything_working_fine(self):
        self.user.create_random_alternative_data()

    def test_value_can_not_be_created_without_flow_before(self):
        with self.assertRaises(ValueError):
            self.create_value(20, 100)

    def test_value_can_not_be_created_far_away_from_flow(self):
        with self.assertRaises(ValueError):
            self.create_flow(21, 100)
            self.create_value(20, 100)

    def test_flow_can_not_be_followed_by_a_flow(self):
        with self.assertRaises(ValueError):
            self.create_flow(20, 100)
            self.create_flow(19, 100)

    def test_value_can_not_be_created_before_flow(self):
        with self.assertRaises(ValueError):
            self.create_flow(20, 100)
            self.create_value(21, 100)

    def test_flow_can_not_be_inserted_next_to_flow(self):
        self.create_flow(20, 100)
        self.create_value(20, 100)
        with self.assertRaises(ValueError):
            self.create_flow(20, 100, hours_before_now=10)
        with self.assertRaises(ValueError):
            self.create_flow(21, 100)
