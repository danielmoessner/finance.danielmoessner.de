from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import ProtectedError
from django.views import generic
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from finance.users.views.views import SettingsView
from finance.core.views import CustomInvalidFormMixin
from finance.core.views import CustomDeleteView
from finance.banking.forms import UpdateDepotForm as EditBankingDepotForm
from finance.banking.forms import CreateDepotForm as AddBankingDepotForm
from finance.crypto.forms import CreateDepotForm as EditCryptoDepotForm
from finance.crypto.forms import CreateDepotForm as AddCryptoDepotForm
from finance.banking.models import Depot as BankingDepot
from finance.crypto.models import Depot as CryptoDepot
from finance.users.models import StandardUser
from finance.users.forms import UpdateStandardUserForm, UpdateCryptoStandardUserForm
from finance.users.forms import UpdateGeneralStandardUserForm
from finance.core.utils import form_invalid_universal


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


# banking
class SettingsAddBankingDepotView(SettingsView, generic.CreateView):
    form_class = AddBankingDepotForm
    model = BankingDepot

    def form_valid(self, form):
        depot = form.save(commit=False)
        depot.user = self.request.user
        depot.save()
        success_url = reverse_lazy("users:settings", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors", heading="Depot could not be created:")


class SettingsEditBankingDepotView(SettingsView):
    def post(self, request, *args, **kwargs):
        form = EditBankingDepotForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        depot_pk = form.cleaned_data["pk"]
        depot = BankingDepot.objects.get(pk=depot_pk)
        depot.name = form.cleaned_data["name"]
        depot.save()
        success_url = reverse_lazy("users:settings", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors", heading="Depot could not be edited.")


class SettingsDeleteBankingDepotView(SettingsView, CustomDeleteView):
    def form_valid(self, form):
        depot_pk = form.cleaned_data["pk"]
        depot = BankingDepot.objects.get(pk=depot_pk)
        try:
            depot.delete()
        except ProtectedError as e:
            context = self.get_context_data()
            context["errors"] = ["Depot could not be deleted.",
                                 "You need to delete the accounts within the depot first."]
            return self.render_to_response(context)
        success_url = reverse_lazy("users:settings", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, **kwargs):
        return form_invalid_universal(self, form, "errors", heading="Depot could not be deleted.")


# crypto
class SettingsAddCryptoDepotView(SettingsView, generic.CreateView):
    form_class = AddCryptoDepotForm
    model = CryptoDepot

    def form_valid(self, form):
        depot = form.save(commit=False)
        depot.user = self.request.user
        depot.save()
        success_url = reverse_lazy("users:settings", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors", heading="Depot could not be created:")


class SettingsEditCryptoDepotView(SettingsView):
    def post(self, request, *args, **kwargs):
        form = EditCryptoDepotForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        depot_pk = form.cleaned_data["pk"]
        depot = CryptoDepot.objects.get(pk=depot_pk)
        depot.name = form.cleaned_data["name"]
        depot.save()
        success_url = reverse_lazy("users:settings", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors", heading="Depot could not be edited:")


class SettingsDeleteCryptoDepotView(SettingsView, CustomDeleteView):
    def form_valid(self, form):
        depot_pk = form.cleaned_data["pk"]
        depot = CryptoDepot.objects.get(pk=depot_pk)
        try:
            depot.delete()
        except ProtectedError as e:
            context = self.get_context_data(**self.request.kwargs)
            context["errors"] = ["Depot could not be deleted.",
                                 "You need to delete the accounts within the depot first."]
            return self.render_to_response(context)
        success_url = reverse_lazy("users:settings", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, **kwargs):
        return form_invalid_universal(self, form, "errors", heading="Depot could not be deleted:")
