from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.urls import reverse_lazy

from finance.crypto.models import Transaction
from finance.crypto.models import Timespan
from finance.crypto.models import Account
from finance.crypto.models import Asset
from finance.crypto.models import Trade
from finance.crypto.models import Depot
from finance.crypto.models import Movie
from finance.crypto.forms import TimespanActiveForm
from finance.crypto.forms import AccountSelectForm
from finance.crypto.forms import AssetSelectForm
from finance.crypto.forms import DepotSelectForm
from finance.crypto.forms import DepotActiveForm
from finance.crypto.forms import TransactionForm
from finance.crypto.forms import TimespanForm
from finance.crypto.forms import AccountForm
from finance.crypto.forms import TradeForm
from finance.crypto.forms import DepotForm
from finance.core.views import CustomAjaxDeleteMixin
from finance.core.views import CustomAjaxFormMixin
from django.http import HttpResponse

import json


# mixins
class CustomGetFormMixin(object):
    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        depot = self.request.user.crypto_depots.get(is_active=True)
        return form_class(depot, **self.get_form_kwargs())


class CustomGetFormUserMixin(object):
    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        user = self.request.user
        return form_class(user, **self.get_form_kwargs())


# depot
class AddDepotView(LoginRequiredMixin, CustomGetFormUserMixin, CustomAjaxFormMixin, generic.CreateView):
    form_class = DepotForm
    model = Depot
    template_name = "modules/form_snippet.njk"


class EditDepotView(LoginRequiredMixin, CustomGetFormUserMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Depot
    form_class = DepotForm
    template_name = "modules/form_snippet.njk"


class DeleteDepotView(LoginRequiredMixin, CustomGetFormUserMixin, CustomAjaxFormMixin, generic.FormView):
    model = Depot
    template_name = "modules/form_snippet.njk"
    form_class = DepotSelectForm

    def form_valid(self, form):
        depot = form.cleaned_data["depot"]
        user = depot.user
        depot.delete()
        if user.crypto_depots.count() <= 0:
            user.crypto_is_active = False
            user.save()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


class SetActiveDepotView(LoginRequiredMixin, CustomGetFormUserMixin, generic.UpdateView):
    model = Depot
    form_class = DepotActiveForm
    template_name = "modules/form_snippet.njk"
    success_url = reverse_lazy("users:settings")


# account
class AddAccountView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    form_class = AccountForm
    model = Account
    template_name = "modules/form_snippet.njk"


class EditAccountView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Account
    form_class = AccountForm
    template_name = "modules/form_snippet.njk"


class DeleteAccountView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.FormView):
    model = Account
    template_name = "modules/form_snippet.njk"
    form_class = AccountSelectForm

    def form_valid(self, form):
        account = form.cleaned_data["account"]
        account.delete()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


# asset
class AddAssetView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.FormView):
    model = Asset
    template_name = "modules/form_snippet.njk"
    form_class = AssetSelectForm

    def form_valid(self, form):
        asset = form.cleaned_data["asset"]
        depot = self.request.user.crypto_depots.get(is_active=True)
        asset.depots.add(depot)
        asset.save()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


class RemoveAssetView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.FormView):
    model = Asset
    template_name = "modules/form_snippet.njk"
    form_class = AssetSelectForm

    def form_valid(self, form):
        asset = form.cleaned_data["asset"]
        depot = self.request.user.crypto_depots.get(is_active=True)
        asset.depots.remove(depot)
        Movie.objects.filter(depot=depot, asset=asset).delete()
        asset.save()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


# trade
class AddTradeView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    model = Trade
    form_class = TradeForm
    template_name = "modules/form_snippet.njk"


class AddTradeAccountView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    model = Trade
    form_class = TradeForm
    template_name = "modules/form_snippet.njk"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        account = Account.objects.get(slug=self.kwargs["slug"])
        kwargs.update({"initial": {"account": account}})
        return kwargs


class EditTradeView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Trade
    form_class = TradeForm
    template_name = "modules/form_snippet.njk"


class DeleteTradeView(LoginRequiredMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Trade
    template_name = "modules/delete_snippet.njk"


# transaction
class AddTransactionView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "modules/form_snippet.njk"


class EditTransactionView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "modules/form_snippet.njk"


class DeleteTransactionView(LoginRequiredMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Transaction
    template_name = "modules/delete_snippet.njk"


# timespan
class AddTimespanView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    form_class = TimespanForm
    model = Timespan
    template_name = "modules/form_snippet.njk"


class SetActiveTimespanView(LoginRequiredMixin, CustomGetFormMixin, generic.UpdateView):
    model = Timespan
    form_class = TimespanActiveForm
    template_name = "modules/form_snippet.njk"
    success_url = reverse_lazy("crypto:index")


class DeleteTimespanView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Timespan
    template_name = "modules/delete_snippet.njk"
    form_class = TimespanForm
