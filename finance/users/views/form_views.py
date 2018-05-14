from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic

from finance.users.forms import EditStandardUserForm, EditStandardUserSpecialsForm
from finance.users.models import StandardUser
from finance.users.views.views import SettingsView
from finance.banking.forms import EditDepotForm as EditBankingDepotForm
from finance.banking.forms import AddDepotForm as AddBankingDepotForm
from finance.banking.models import Depot as BankingDepot
from finance.crypto.forms import AddDepotForm as EditCryptoDepotForm
from finance.crypto.forms import AddDepotForm as AddCryptoDepotForm
from finance.crypto.models import Depot as CryptoDepot
from finance.core.utils import form_invalid_universal
from finance.core.views import CustomDeleteView


class SettingsEditUserSpecialsView(SettingsView, generic.UpdateView):
    form_class = EditStandardUserSpecialsForm
    model = StandardUser

    def form_valid(self, form):
        # form is invalid if this is true
        if form.cleaned_data["currency"] != self.request.user.currency:
            context = self.get_context_data()
            context["errors"] = [
                "At the moment it's not allowed to change the currency once it was set.",
            ]
            return self.render_to_response(context)
        # form valid
        self.success_url = reverse_lazy("users:settings", args=[self.request.user.slug, ])
        return super(SettingsEditUserSpecialsView, self).form_valid(form)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="User data could not be edited:")


class SettingsEditUserView(SettingsView, generic.UpdateView):
    form_class = EditStandardUserForm
    model = StandardUser

    def form_valid(self, form):
        self.success_url = reverse_lazy("users:settings", args=[self.request.user.slug, ])
        return super(SettingsEditUserView, self).form_valid(form)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="User data could not be edited:")


class SettingsEditUserPasswordView(SettingsView, generic.UpdateView):
    form_class = PasswordChangeForm
    model = StandardUser

    def form_valid(self, form):
        self.success_url = reverse_lazy("users:settings", args=[self.request.user.slug, ])
        return super(SettingsEditUserPasswordView, self).form_valid(form)

    def post(self, request, *args, **kwargs):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="Password could not be changed:")


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
        return form_invalid_universal(self, form, "errors", heading="Depot could not be edited:")


class SettingsDeleteBankingDepotView(SettingsView, CustomDeleteView):
    def form_valid(self, form):
        depot_pk = form.cleaned_data["pk"]
        depot = BankingDepot.objects.get(pk=depot_pk)
        depot.delete()
        success_url = reverse_lazy("users:settings", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors", heading="Depot could not be deleted:")


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
        depot.delete()
        success_url = reverse_lazy("users:settings", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors", heading="Depot could not be deleted:")

