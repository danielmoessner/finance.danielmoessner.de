from apps.alternative.models import Alternative, Depot
from apps.alternative.forms import ValueForm, FlowForm
from apps.users.models import StandardUser as User
from django.test import TestCase, Client
from django.urls import reverse_lazy


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

    def create_flow(self, date, flow):
        flow = FlowForm(self.depot, {"alternative": self.alternative.pk, "date": date, "flow": flow})
        flow.save()
        return flow

    def create_value(self, date, value):
        value = ValueForm(self.depot, {"alternative": self.alternative.pk, "date": date, "value": value})
        value.save()
        return value

    def test_everything_working_fine(self):
        self.user.create_random_alternative_data()

    def test_value_can_not_be_created_without_flow_before(self):
        with self.assertRaises(ValueError):
            self.create_value("2020-05-05T13:30", 100)

    def test_value_can_not_be_created_far_away_from_flow(self):
        self.create_flow('2020-05-05T13:30', 100)
        with self.assertRaises(ValueError):
            self.create_value('2020-05-06T13:31', 100)

    def test_flow_can_not_be_followed_by_a_flow(self):
        self.create_flow('2020-05-05T13:30', 100)
        with self.assertRaises(ValueError):
            self.create_flow('2020-05-05T13:33', 100)

    def test_value_can_not_be_created_before_flow(self):
        self.create_flow('2020-05-05T13:30', 100)
        with self.assertRaises(ValueError):
            self.create_value('2020-05-04T13:30', 100)

    def test_flow_can_not_be_inserted_next_to_flow(self):
        self.create_flow('2020-05-05T13:30', 100)
        self.create_value('2020-05-05T13:32', 100)
        with self.assertRaises(ValueError):
            self.create_flow('2020-05-05T13:31', 100)
        with self.assertRaises(ValueError):
            self.create_flow('2020-05-05T13:29', 100)

    def test_value_or_flow_can_not_be_on_the_same_date(self):
        self.create_flow('2020-05-05T13:30', 100)
        with self.assertRaises(ValueError):
            self.create_value('2020-05-05T13:30', 100)
        self.create_value('2020-05-05T13:31', 100)
        with self.assertRaises(ValueError):
            self.create_flow('2020-05-05T13:31', 100)
