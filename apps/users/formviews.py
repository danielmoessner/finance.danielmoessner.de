from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView
from django.views import generic

from apps.users.models import StandardUser
from apps.users.forms import UpdateGeneralStandardUserForm
from apps.users.forms import UpdateCryptoStandardUserForm
from apps.users.forms import UpdateStandardUserForm
from apps.core.views import AjaxResponseMixin


class UserIsLoggedIn(UserPassesTestMixin):
    def test_func(self):
        return self.get_object() == self.request.user


class EditUserSettingsView(UserIsLoggedIn, AjaxResponseMixin, generic.UpdateView):
    form_class = UpdateStandardUserForm
    model = StandardUser
    template_name = "modules/form_snippet.njk"


class EditUserPasswordSettingsView(AjaxResponseMixin, PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = "modules/form_snippet.njk"


class EditUserGeneralSettingsView(UserIsLoggedIn, AjaxResponseMixin, generic.UpdateView):
    form_class = UpdateGeneralStandardUserForm
    model = StandardUser
    template_name = "modules/form_snippet.njk"


class EditUserCryptoSettingsView(UserIsLoggedIn, AjaxResponseMixin, generic.UpdateView):
    form_class = UpdateCryptoStandardUserForm
    model = StandardUser
    template_name = "modules/form_snippet.njk"
