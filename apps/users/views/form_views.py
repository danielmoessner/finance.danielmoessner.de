from django.contrib.auth.forms import PasswordChangeForm
from django.views import generic
from django.urls import reverse_lazy

from apps.users.views.views import SettingsView
from apps.users.models import StandardUser
from apps.users.forms import UpdateGeneralStandardUserForm
from apps.users.forms import UpdateCryptoStandardUserForm
from apps.users.forms import UpdateStandardUserForm
from apps.core.views import CustomInvalidFormMixin


# user
class EditUserSettingsView(SettingsView, CustomInvalidFormMixin, generic.UpdateView):
    form_class = UpdateStandardUserForm
    model = StandardUser
    success_url = reverse_lazy("users:settings")

    def get_context_data(self, **kwargs):
        context = super(EditUserSettingsView, self).get_context_data()
        context["edit_user_form"] = self.get_form()
        return context


class EditUserPasswordSettingsView(SettingsView, CustomInvalidFormMixin, generic.UpdateView):
    form_class = PasswordChangeForm
    model = StandardUser
    success_url = reverse_lazy("users:settings")

    def post(self, request, *args, **kwargs):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(EditUserPasswordSettingsView, self).get_context_data()
        context["edit_user_password_form"] = self.get_form()
        return context


class EditUserGeneralSettingsView(SettingsView, CustomInvalidFormMixin, generic.UpdateView):
    form_class = UpdateGeneralStandardUserForm
    model = StandardUser
    success_url = reverse_lazy("users:settings")

    def get_context_data(self, **kwargs):
        context = super(EditUserGeneralSettingsView, self).get_context_data()
        context["edit_user_general_form"] = self.get_form()
        return context


class EditUserCryptoSettingsView(SettingsView, CustomInvalidFormMixin, generic.UpdateView):
    form_class = UpdateCryptoStandardUserForm
    model = StandardUser
    success_url = reverse_lazy("users:settings")

    def get_context_data(self, **kwargs):
        context = super(EditUserCryptoSettingsView, self).get_context_data()
        context["edit_user_crypto_form"] = self.get_form()
        return context
