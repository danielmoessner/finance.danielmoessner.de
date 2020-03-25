from rest_framework.test import APIClient
from django.utils import timezone
from django.urls import reverse_lazy
from django.test import TestCase
from django.test import Client

from apps.banking.models import Depot, Category, Account, Change
from apps.banking.forms import ChangeForm, AccountForm, DepotForm, CategoryForm
from apps.users.models import StandardUser as User

from datetime import timedelta


def create_account(depot, name=None):
    form = AccountForm(depot, {'name': name})
    assert form.is_valid()
    return form.save()


def create_category(depot, name=None, description=''):
    form = CategoryForm(depot, {'name': name, 'description': description})
    assert form.is_valid()
    return form.save()


def create_depot(user, name=None):
    form = DepotForm(user, {'name': name})
    assert form.is_valid()
    return form.save()


def create_change(depot, account=None, category=None, date=None, change=10, description=''):
    form = ChangeForm(depot, {'account': account,
                              'category': category, 'date': date, 'change': change, 'description': description})
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

    def test_account_view(self):
        self.client = Client()
        self.client.login(username="dummy", password="test")
        self.user = User.objects.get(username="dummy")
        account = self.user.banking_depots.get(is_active=True).accounts.first()
        response = self.client.get(reverse_lazy("banking:account", args=[account.pk]))
        self.assertEqual(response.status_code, 200)

    def test_category_view(self):
        self.client = Client()
        self.client.login(username="dummy", password="test")
        self.user = User.objects.get(username="dummy")
        category = self.user.banking_depots.get(is_active=True).categories.first()
        response = self.client.get(reverse_lazy("banking:category", args=[category.pk]))
        self.assertEqual(response.status_code, 200)


class BalanceUpdateTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dummy")
        self.user.set_password("test")
        self.user.save()
        self.depot_pk = create_depot(self.user, 'Depot').pk
        self.account_pk = create_account(self.get_depot(), 'Account').pk
        self.category_pk = create_category(self.get_depot(), 'Category').pk

    def get_account(self):
        return Account.objects.get(pk=self.account_pk)

    def get_category(self):
        return Category.objects.get(pk=self.category_pk)

    def get_depot(self):
        return Depot.objects.get(pk=self.depot_pk)

    def create_change_and_set_balances(self, days_ago=20):
        date_x_days_ago = timezone.now() - timedelta(days=days_ago)
        change = create_change(self.get_depot(), account=self.get_account(), category=self.get_category(),
                               date=date_x_days_ago)
        # set the balances
        self.get_account().get_stats()
        self.get_depot().get_stats()
        self.get_category().get_stats()
        # return the change
        return change

    def test_balance_is_set_properly(self):
        change = self.create_change_and_set_balances()
        # test that stats are being set properly
        assert self.get_account().balance is not None
        assert self.get_depot().balance is not None
        assert self.get_category().balance is not None

    def test_balance_is_reset_properly_after_change_added(self):
        change = self.create_change_and_set_balances(days_ago=20)
        # test that balances are reset properly after a change is added
        days_ago_10 = timezone.now() - timedelta(days=10)
        change = create_change(self.get_depot(), account=self.get_account(), category=self.get_category(),
                               date=days_ago_10)
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


class APITestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dummy")
        self.user.set_password("test")
        self.user.save()
        self.user.create_random_banking_data()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_api_access_not_allowed_if_not_logged_in(self):
        self.client.force_authenticate()
        urls = [
            '/banking/api/categories/',
            '/banking/api/accounts/',
            '/banking/api/changes/',
            '/banking/api/depots/',
            '/banking/api/changes/1/',
            '/banking/api/categories/1/',
            '/banking/api/depots/1/',
            '/banking/api/accounts/1/',
        ]
        for url in urls:
            response = self.client.get(url)
            # check that access is forbidden
            assert response.status_code == 403

    def post_depot(self):
        data = {
            'user': self.user.id,
            'name': 'Test Depot'
        }
        return self.client.post('/banking/api/depots/', data, format='json')

    def post_category(self, depot=1):
        data = {
            'depot': '/banking/api/depots/{}/'.format(depot),
            'name': 'Test Category',
            'description': 'Just testing.'
        }
        return self.client.post('/banking/api/categories/', data, format='json')

    def post_account(self):
        data = {
            'depot': '/banking/api/depots/1/',
            'name': 'Test Account'
        }
        return self.client.post('/banking/api/accounts/', data, format='json')

    def post_change(self):
        data = {
            'change': '50',
            'description': 'Test Change',
            'account': '/banking/api/accounts/1/',
            'date': '2018-06-19T13:54',
            'category': '/banking/api/categories/1/'
        }
        return self.client.post('/banking/api/changes/', data, format='json')

    def test_post_working_when_it_should(self):
        response = self.post_category()
        assert response.status_code == 201
        response = self.post_account()
        assert response.status_code == 201
        response = self.post_change()
        assert response.status_code == 201
        response = self.post_depot()
        assert response.status_code == 201

    def test_patch_working_when_it_should(self):
        data = {
            'name': 'Test Category'
        }
        response = self.client.patch('/banking/api/categories/1/', data, format='json')
        assert response.status_code == 200
        data = {
            'name': 'Test Account'
        }
        response = self.client.patch('/banking/api/accounts/1/', data, format='json')
        assert response.status_code == 200
        data = {
            'change': '150'
        }
        response = self.client.patch('/banking/api/changes/1/', data, format='json')
        assert response.status_code == 200
        data = {
            'name': 'Test Depot'
        }
        response = self.client.patch('/banking/api/depots/1/', data, format='json')
        assert response.status_code == 200

    def test_get_working_when_it_should(self):
        urls = [
            '/banking/api/',
            '/banking/api/categories/',
            '/banking/api/accounts/',
            '/banking/api/changes/',
            '/banking/api/depots/',
            '/banking/api/changes/1/',
            '/banking/api/categories/1/',
            '/banking/api/depots/1/',
            '/banking/api/accounts/1/',
        ]
        for url in urls:
            response = self.client.get(url)
            assert response.status_code == 200

    def test_put_working_when_it_should(self):
        data = {
            'depot': '/banking/api/depots/1/',
            'name': 'Test Category 2',
            'description': 'Just testing 2.'
        }
        response = self.client.put('/banking/api/categories/1/', data, format='json')
        assert response.status_code == 200
        data = {
            'depot': '/banking/api/depots/1/',
            'name': 'Test Account 2'
        }
        response = self.client.put('/banking/api/accounts/1/', data, format='json')
        assert response.status_code == 200
        data = {
            'change': '150',
            'description': 'Test Change 2',
            'account': '/banking/api/accounts/2/',
            'date': '2018-06-19T13:54',
            'category': '/banking/api/categories/1/'
        }
        response = self.client.put('/banking/api/changes/1/', data, format='json')
        assert response.status_code == 200
        data = {
            'user': self.user.id,
            'name': 'Test Depot'
        }
        response = self.client.put('/banking/api/depots/1/', data, format='json')
        assert response.status_code == 200

    def test_post_not_allowing_stupid_data(self):
        response = self.post_depot()
        assert response.status_code == 201
        first_depot = Depot.objects.all().first()
        second_depot = Depot.objects.all().last()
        self.assertNotEqual(first_depot, second_depot)
        account = first_depot.accounts.first()
        response = self.post_category(depot=second_depot.id)
        assert response.status_code == 201
        category = second_depot.categories.first()
        data = {
            'change': '150',
            'description': 'Test Change 2',
            'account': '/banking/api/accounts/{}/'.format(account.id),
            'date': '2018-06-19T13:54',
            'category': '/banking/api/categories/{}/'.format(category.id)
        }
        response = self.client.post('/banking/api/changes/', data, format='json')
        assert response.status_code == 400

    def test_delete_not_working_on_account_and_categories_that_contain_changes(self):
        response = self.client.delete('/banking/api/categories/1/')
        assert response.status_code == 400
        repsonse = self.client.delete('/banking/api/accounts/1')
        assert response.status_code == 400

    def test_delete_working_on_account_and_categories_without_changes(self):
        Category.objects.get(pk=1).changes.all().delete()
        response = response = self.client.delete('/banking/api/categories/1/')
        assert response.status_code == 204
        Account.objects.get(pk=1).changes.all().delete()
        repsonse = self.client.delete('/banking/api/accounts/1')
        assert response.status_code == 204
