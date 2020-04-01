from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views import generic
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy

from apps.crypto.models import Transaction, Flow, Timespan, Account, Asset, Trade, Depot
from apps.crypto.forms import TimespanActiveForm, FlowForm, AccountSelectForm, TradeForm, DepotForm, AccountForm
from apps.crypto.forms import AssetSelectForm, DepotSelectForm, DepotActiveForm, TransactionForm, TimespanForm
from apps.core.views import CustomAjaxDeleteMixin, CustomAjaxResponseMixin, CustomGetFormUserMixin

import json


# mixins
class CustomGetFormMixin:
    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        depot = self.request.user.crypto_depots.get(is_active=True)
        return form_class(depot, **self.get_form_kwargs())


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


class DeleteAssetView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.FormView):
    model = Asset
    template_name = "modules/form_snippet.njk"
    form_class = AssetSelectForm

    def form_valid(self, form):
        asset = form.cleaned_data["asset"]
        asset.delete()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


# trade
class AddTradeView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.CreateView):
    model = Trade
    form_class = TradeForm
    template_name = "modules/form_snippet.njk"


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


# flow
class AddFlowView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.CreateView):
    model = Flow
    form_class = FlowForm
    template_name = "modules/form_snippet.njk"

    def get_form(self, form_class=None):
        depot = self.request.user.crypto_depots.get(is_active=True)
        if form_class is None:
            form_class = self.get_form_class()
        if self.request.method == 'GET':
            return form_class(depot, initial=self.request.GET, **self.get_form_kwargs().pop('initial'))
        return form_class(depot, **self.get_form_kwargs())


class EditFlowView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.UpdateView):
    model = Flow
    form_class = FlowForm
    template_name = "modules/form_snippet.njk"


class DeleteFlowView(LoginRequiredMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Flow
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
