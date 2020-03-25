from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views import generic
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from apps.crypto.models import Transaction
from apps.crypto.models import Timespan
from apps.crypto.models import Account
from apps.crypto.models import Asset
from apps.crypto.models import Trade
from apps.crypto.models import Depot
from apps.crypto.models import Movie
from apps.crypto.forms import TimespanActiveForm
from apps.crypto.forms import AccountSelectForm
from apps.crypto.forms import AssetSelectForm
from apps.crypto.forms import DepotSelectForm
from apps.crypto.forms import DepotActiveForm
from apps.crypto.forms import TransactionForm
from apps.crypto.forms import TimespanForm
from apps.crypto.forms import AccountForm
from apps.crypto.forms import TradeForm
from apps.crypto.forms import DepotForm
from apps.core.views import CustomAjaxDeleteMixin
from apps.core.views import CustomAjaxResponseMixin
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
class AddDepotView(LoginRequiredMixin, CustomGetFormUserMixin, CustomAjaxResponseMixin, generic.CreateView):
    form_class = DepotForm
    model = Depot
    template_name = "modules/form_snippet.njk"


class EditDepotView(LoginRequiredMixin, CustomGetFormUserMixin, CustomAjaxResponseMixin, generic.UpdateView):
    model = Depot
    form_class = DepotForm
    template_name = "modules/form_snippet.njk"


class DeleteDepotView(LoginRequiredMixin, CustomGetFormUserMixin, CustomAjaxResponseMixin, generic.FormView):
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


class SetActiveDepotView(LoginRequiredMixin, generic.View):
    http_method_names = ['get', 'head', 'options']

    def get(self, request, pk, *args, **kwargs):
        depot = get_object_or_404(self.request.user.crypto_depots.all(), pk=pk)
        form = DepotActiveForm(data={'is_active': True}, instance=depot)
        if form.is_valid():
            form.save()
        url = '{}?tab=crypto'.format(reverse_lazy('users:settings', args=[self.request.user.pk]))
        return HttpResponseRedirect(url)


# account
class AddAccountView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.CreateView):
    form_class = AccountForm
    model = Account
    template_name = "modules/form_snippet.njk"


class EditAccountView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.UpdateView):
    model = Account
    form_class = AccountForm
    template_name = "modules/form_snippet.njk"


class DeleteAccountView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.FormView):
    model = Account
    template_name = "modules/form_snippet.njk"
    form_class = AccountSelectForm

    def form_valid(self, form):
        account = form.cleaned_data["account"]
        account.delete()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


# asset
class AddAssetView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.FormView):
    model = Asset
    template_name = "modules/form_snippet.njk"
    form_class = AssetSelectForm

    def form_valid(self, form):
        asset = form.cleaned_data["asset"]
        depot = self.request.user.crypto_depots.get(is_active=True)
        asset.depots.add(depot)
        asset.save()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


class RemoveAssetView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.FormView):
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
class AddTradeView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.CreateView):
    model = Trade
    form_class = TradeForm
    template_name = "modules/form_snippet.njk"


class AddTradeAccountView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.CreateView):
    model = Trade
    form_class = TradeForm
    template_name = "modules/form_snippet.njk"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        account = Account.objects.get(slug=self.kwargs["slug"])
        kwargs.update({"initial": {"account": account}})
        return kwargs


class EditTradeView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.UpdateView):
    model = Trade
    form_class = TradeForm
    template_name = "modules/form_snippet.njk"


class DeleteTradeView(LoginRequiredMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Trade
    template_name = "modules/delete_snippet.njk"


# transaction
class AddTransactionView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "modules/form_snippet.njk"


class EditTransactionView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "modules/form_snippet.njk"


class DeleteTransactionView(LoginRequiredMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Transaction
    template_name = "modules/delete_snippet.njk"


# timespan
class AddTimespanView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.CreateView):
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
