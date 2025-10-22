from typing import Callable

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView
from django.db import models
from django.http import HttpRequest
from django.views import generic

from apps.core.mixins import AjaxResponseMixin
from apps.users.forms import (
    UpdateCryptoStandardUserForm,
    UpdateGeneralStandardUserForm,
    UpdateStandardUserForm,
)
from apps.users.models import StandardUser


class UserIsLoggedIn(UserPassesTestMixin):
    get_object: Callable[[], models.Model]
    request: HttpRequest

    def test_func(self):
        return self.get_object() == self.request.user


class EditUserSettingsView(UserIsLoggedIn, AjaxResponseMixin, generic.UpdateView):
    form_class = UpdateStandardUserForm
    model = StandardUser
    template_name = "symbols/form_snippet.j2"


class EditUserPasswordSettingsView(AjaxResponseMixin, PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = "symbols/form_snippet.j2"


class EditUserGeneralSettingsView(
    UserIsLoggedIn, AjaxResponseMixin, generic.UpdateView
):
    form_class = UpdateGeneralStandardUserForm
    model = StandardUser
    template_name = "symbols/form_snippet.j2"


class EditUserCryptoSettingsView(UserIsLoggedIn, AjaxResponseMixin, generic.UpdateView):
    form_class = UpdateCryptoStandardUserForm
    model = StandardUser
    template_name = "symbols/form_snippet.j2"
