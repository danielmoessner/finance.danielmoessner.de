import pytest
from django.test import Client
from django.urls import reverse_lazy

from apps.users.models import StandardUser as User


@pytest.fixture
def user(db):
    user = User.objects.create_user(username="dummy")  # type: ignore
    user.set_password("test")
    user.save()
    user.create_random_banking_data()
    yield user


def test_login_view():
    client = Client()
    response = client.get(reverse_lazy("users:signin"))
    assert response.status_code == 200


def test_signup_view():
    client = Client()
    response = client.get(reverse_lazy("users:signup"))
    assert response.status_code == 200


def test_index_view(user):
    client = Client()
    client.login(username="dummy", password="test")
    response = client.get(reverse_lazy("users:settings", args=[user.pk]))
    assert response.status_code == 200
    url = "{}?tab=banking".format(reverse_lazy("users:settings", args=[user.pk]))
    response = client.get(url)
    assert response.status_code == 200
    response = client.get(
        "{}?tab=alternative".format(reverse_lazy("users:settings", args=[user.pk]))
    )
    assert response.status_code == 200
    response = client.get(
        "{}?tab=crypto".format(reverse_lazy("users:settings", args=[user.pk]))
    )
    assert response.status_code == 200


def test_init_works(user):
    client = Client()
    client.login(username="dummy", password="test")
    response = client.get(reverse_lazy("users:init_banking", args=[user.pk]))
    assert response.status_code == 302
    response = client.get(reverse_lazy("users:init_alternative", args=[user.pk]))
    assert response.status_code == 302
