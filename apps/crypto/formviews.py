import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from apps.core.mixins import (
    AjaxResponseMixin,
    CustomAjaxDeleteMixin,
    CustomGetFormUserMixin,
    GetFormWithDepotAndInitialDataMixin,
    GetFormWithDepotMixin,
)
from apps.crypto.forms import (
    AccountForm,
    AccountSelectForm,
    AssetForm,
    AssetSelectForm,
    DepotActiveForm,
    DepotForm,
    DepotSelectForm,
    FlowForm,
    PriceEditForm,
    PriceFetcherForm,
    TradeForm,
    TransactionForm,
)
from apps.crypto.models import (
    Account,
    Asset,
    Depot,
    Flow,
    Price,
    PriceFetcher,
    Trade,
    Transaction,
)
from apps.users.mixins import GetUserMixin


# mixins
class CustomGetFormMixin:
    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        depot = self.request.user.crypto_depots.get(is_active=True)
        return form_class(depot, **self.get_form_kwargs())


class GetDepotMixin:
    def get_depot(self):
        return self.request.user.crypto_depots.filter(is_active=True).first()


# depot
class AddDepotView(
    LoginRequiredMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.CreateView
):
    form_class = DepotForm
    model = Depot
    template_name = "symbols/form_snippet.j2"


class EditDepotView(
    LoginRequiredMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Depot
    form_class = DepotForm
    template_name = "symbols/form_snippet.j2"


class DeleteDepotView(
    LoginRequiredMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.FormView
):
    model = Depot
    template_name = "symbols/form_snippet.j2"
    form_class = DepotSelectForm

    def form_valid(self, form):
        depot = form.cleaned_data["depot"]
        user = depot.user
        depot.delete()
        if user.crypto_depots.count() <= 0:
            user.save()
        return HttpResponse(
            json.dumps({"valid": True}), content_type="application/json"
        )


class SetActiveDepotView(GetUserMixin, SingleObjectMixin, generic.View):
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        return self.get_user().crypto_depots.all()

    def get(self, request, pk, *args, **kwargs):
        self.get_user().crypto_depots.update(is_active=False)
        depot = self.get_object()
        form = DepotActiveForm(data={"is_active": True}, instance=depot)
        if form.is_valid():
            form.save()
        url = "{}?tab=crypto".format(
            reverse_lazy("users:settings", args=[self.request.user.pk])
        )
        return HttpResponseRedirect(url)


# account
class AddAccountView(
    LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.CreateView
):
    form_class = AccountForm
    model = Account
    template_name = "symbols/form_snippet.j2"


class EditAccountView(
    LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Account
    form_class = AccountForm
    template_name = "symbols/form_snippet.j2"


class DeleteAccountView(
    LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.FormView
):
    model = Account
    template_name = "symbols/form_snippet.j2"
    form_class = AccountSelectForm

    def form_valid(self, form):
        account = form.cleaned_data["account"]
        account.delete()
        return HttpResponse(
            json.dumps({"valid": True}), content_type="application/json"
        )


# asset
class AddAssetView(
    LoginRequiredMixin,
    GetDepotMixin,
    GetFormWithDepotMixin,
    AjaxResponseMixin,
    generic.CreateView,
):
    model = Asset
    template_name = "symbols/form_snippet.j2"
    form_class = AssetForm


class EditAssetView(
    LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Asset
    template_name = "symbols/form_snippet.j2"
    form_class = AssetForm


class DeleteAssetView(
    LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.FormView
):
    model = Asset
    template_name = "symbols/form_snippet.j2"
    form_class = AssetSelectForm

    def form_valid(self, form):
        asset = form.cleaned_data["asset"]
        asset.delete()
        return HttpResponse(
            json.dumps({"valid": True}), content_type="application/json"
        )


# trade
class AddTradeView(
    LoginRequiredMixin,
    GetDepotMixin,
    GetFormWithDepotAndInitialDataMixin,
    AjaxResponseMixin,
    generic.CreateView,
):
    model = Trade
    form_class = TradeForm
    template_name = "symbols/form_snippet.j2"


class EditTradeView(
    LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Trade
    form_class = TradeForm
    template_name = "symbols/form_snippet.j2"


class DeleteTradeView(LoginRequiredMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Trade
    template_name = "symbols/delete_snippet.j2"


###
# Price: Edit, Delete
###
class EditPriceView(LoginRequiredMixin, AjaxResponseMixin, generic.UpdateView):
    model = Price
    form_class = PriceEditForm
    template_name = "symbols/form_snippet.j2"


class DeletePriceView(LoginRequiredMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Price
    template_name = "symbols/delete_snippet.j2"

    def get_queryset(self):
        return Price.objects.filter(
            symbol__in=Asset.objects.filter(
                depot=self.request.user.get_active_crypto_depot()
            ).values_list("symbol", flat=True)
        )


# transaction
class AddTransactionView(
    LoginRequiredMixin,
    GetDepotMixin,
    GetFormWithDepotAndInitialDataMixin,
    AjaxResponseMixin,
    generic.CreateView,
):
    model = Transaction
    form_class = TransactionForm
    template_name = "symbols/form_snippet.j2"


class EditTransactionView(
    LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Transaction
    form_class = TransactionForm
    template_name = "symbols/form_snippet.j2"


class DeleteTransactionView(
    LoginRequiredMixin, CustomAjaxDeleteMixin, generic.DeleteView
):
    model = Transaction
    template_name = "symbols/delete_snippet.j2"


# flow
class AddFlowView(
    LoginRequiredMixin,
    GetDepotMixin,
    GetFormWithDepotAndInitialDataMixin,
    AjaxResponseMixin,
    generic.CreateView,
):
    model = Flow
    form_class = FlowForm
    template_name = "symbols/form_snippet.j2"


class EditFlowView(
    LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Flow
    form_class = FlowForm
    template_name = "symbols/form_snippet.j2"


class DeleteFlowView(LoginRequiredMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Flow
    template_name = "symbols/delete_snippet.j2"


###
# CryptoPriceFetcher: Add, Edit, Delete, Run
###
class AddPriceFetcherView(
    LoginRequiredMixin,
    GetDepotMixin,
    GetFormWithDepotAndInitialDataMixin,
    AjaxResponseMixin,
    generic.CreateView,
):
    form_class = PriceFetcherForm
    model = PriceFetcher
    template_name = "symbols/form_snippet.j2"


class EditPriceFetcherView(
    LoginRequiredMixin,
    GetDepotMixin,
    GetFormWithDepotMixin,
    AjaxResponseMixin,
    generic.UpdateView,
):
    model = PriceFetcher
    form_class = PriceFetcherForm
    template_name = "symbols/form_snippet.j2"


class DeletePriceFetcherView(
    LoginRequiredMixin, CustomAjaxDeleteMixin, generic.DeleteView
):
    model = PriceFetcher
    template_name = "symbols/delete_snippet.j2"

    def get_queryset(self):
        return PriceFetcher.objects.filter(
            asset__in=Asset.objects.filter(
                depot=self.request.user.get_active_crypto_depot()
            )
        )


class RunPriceFetcherView(LoginRequiredMixin, generic.View):
    http_method_names = ["get", "head", "options"]

    def get(self, request, pk, *args, **kwargs):
        fetcher = get_object_or_404(PriceFetcher, pk=pk)
        success, result = fetcher.run()
        if not success:
            assert isinstance(result, str)
            messages.error(request, result)
        url = "{}?tab=prices".format(
            reverse_lazy("crypto:asset", args=[fetcher.asset.pk])
        )
        return HttpResponseRedirect(url)
