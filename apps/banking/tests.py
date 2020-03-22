from rest_framework.test import APIClient
from django.urls import reverse_lazy
from django.test import TestCase
from django.test import Client

from apps.users.models import StandardUser as User
from apps.banking.models import Depot, Category, Account


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
        response = self.client.get(reverse_lazy("banking:account", args=[account.slug]))
        self.assertEqual(response.status_code, 200)

    def test_category_view(self):
        self.client = Client()
        self.client.login(username="dummy", password="test")
        self.user = User.objects.get(username="dummy")
        category = self.user.banking_depots.get(is_active=True).categories.first()
        response = self.client.get(reverse_lazy("banking:category", args=[category.slug]))
        self.assertEqual(response.status_code, 200)


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
