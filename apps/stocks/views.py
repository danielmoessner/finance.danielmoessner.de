import json

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic

from apps.users.mixins import GetUserMixin

from .forms import (
    BankForm,
    BankSelectForm,
    DepotActiveForm,
    DepotForm,
    DepotSelectForm,
    DividendForm,
    EditStockForm,
    FlowForm,
    PriceEditForm,
    PriceFetcherForm,
    StockForm,
    StockSelectForm,
    TradeForm,
)
from .mixins import GetDepotMixin
from .models import Bank, Depot, Dividend, Flow, Price, PriceFetcher, Stock, Trade
from apps.core.mixins import (
    AjaxResponseMixin,
    CustomAjaxDeleteMixin,
    CustomGetFormUserMixin,
    GetFormWithDepotAndInitialDataMixin,
    GetFormWithDepotMixin,
    TabContextMixin,
)
from apps.users.models import StandardUser


###
# Depot: Detail, Create, Edit, Delete, SetActive
###
class IndexView(GetUserMixin, TabContextMixin, generic.DetailView):
    template_name = "stocks/index.j2"
    model = Depot
    object: Depot

    def get_object(self, _=None) -> Depot | None:
        user: StandardUser = self.get_user()  # type: ignore
        return user.get_active_stocks_depot()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = self.object.get_stats()
        context["banks"] = self.object.banks.order_by("-value", "name")
        context["stocks"] = self.object.stocks.select_related(
            "price", "top_price"
        ).order_by("-value", "name")
        context["values"] = self.object.get_values()
        context["flows"] = self.object.get_flows()
        return context


class CreateDepotView(
    GetUserMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.CreateView
):
    template_name = "symbols/form_snippet.j2"
    model = Depot
    form_class = DepotForm


class EditDepotView(
    GetUserMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Depot
    form_class = DepotForm
    template_name = "symbols/form_snippet.j2"


class DeleteDepotView(
    GetUserMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.FormView
):
    model = Depot
    template_name = "symbols/form_snippet.j2"
    form_class = DepotSelectForm

    def form_valid(self, form):
        depot = form.cleaned_data["depot"]
        user = depot.user
        depot.delete()
        if user.stock_depots.count() <= 0:
            user.save()
        return HttpResponse(
            json.dumps({"valid": True}), content_type="application/json"
        )


class ResetDepotView(GetUserMixin, generic.View):
    def post(self, request, pk, *args, **kwargs):
        depot = self.get_user().stock_depots.get(pk=pk)
        depot.reset_all()
        return HttpResponseRedirect(reverse_lazy("stocks:index"))


class SetActiveDepotView(GetUserMixin, generic.View):
    http_method_names = ["get", "head", "options"]

    def get(self, request, pk, *args, **kwargs):
        self.get_user().stock_depots.update(is_active=False)
        depot = get_object_or_404(self.get_user().stock_depots.all(), pk=pk)
        form = DepotActiveForm(data={"is_active": True}, instance=depot)
        if form.is_valid():
            depot = form.save()
        url = "{}?tab=stocks".format(
            reverse_lazy("users:settings", args=[self.get_user().pk])
        )
        return HttpResponseRedirect(url)


###
# Stock: Detail, Add, Edit, Delete
###
class StockView(GetUserMixin, TabContextMixin, generic.DetailView):
    template_name = "stocks/stock.j2"
    model = Stock
    object: Stock

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["trades"] = self.object.trades.all().select_related("bank", "stock")
        context["stats"] = self.object.get_stats()
        context["prices"] = Price.objects.filter(
            ticker=self.object.ticker, exchange=self.object.exchange
        )
        context["dividends"] = self.object.dividends.all()
        context["values"] = self.object.get_values()
        context["flows"] = self.object.get_flows()
        context["fetchers"] = self.object.price_fetchers.all()
        return context


class AddStockView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotMixin,
    AjaxResponseMixin,
    generic.CreateView,
):
    form_class = StockForm
    model = Stock
    template_name = "symbols/form_snippet.j2"


class EditStockView(
    GetUserMixin, GetDepotMixin, GetFormWithDepotMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Stock
    form_class = EditStockForm
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return Stock.objects.filter(depot__in=self.get_user().stock_depots.all())


class DeleteStockView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotMixin,
    AjaxResponseMixin,
    generic.FormView,
):
    model = Stock
    template_name = "symbols/form_snippet.j2"
    form_class = StockSelectForm

    def form_valid(self, form):
        stock = form.cleaned_data["stock"]
        stock.delete()
        return HttpResponse(
            json.dumps({"valid": True}), content_type="application/json"
        )


###
# Price: Edit, Delete
###
class EditPriceView(GetUserMixin, AjaxResponseMixin, generic.UpdateView):
    model = Price
    form_class = PriceEditForm
    template_name = "symbols/form_snippet.j2"


class DeletePriceView(GetUserMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Price
    template_name = "symbols/delete_snippet.j2"

    def get_queryset(self):
        return Price.objects.filter(
            ticker__in=Stock.objects.filter(
                depot=self.get_user().get_active_stocks_depot()
            ).values_list("ticker", flat=True)
        )


###
# StockPriceFetcher: Add, Edit, Delete, Run
###
class AddPriceFetcherView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotAndInitialDataMixin,
    AjaxResponseMixin,
    generic.CreateView,
):
    form_class = PriceFetcherForm
    model = PriceFetcher
    template_name = "symbols/form_snippet.j2"


class EditPriceFetcherView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotMixin,
    AjaxResponseMixin,
    generic.UpdateView,
):
    model = PriceFetcher
    form_class = PriceFetcherForm
    template_name = "symbols/form_snippet.j2"


class DeletePriceFetcherView(
    GetUserMixin, CustomAjaxDeleteMixin, generic.DeleteView
):
    model = PriceFetcher
    template_name = "symbols/delete_snippet.j2"

    def get_queryset(self):
        return PriceFetcher.objects.filter(
            stock__in=Stock.objects.filter(
                depot=self.get_user().get_active_stocks_depot()
            )
        )


class RunPriceFetcherView(GetUserMixin, generic.View):
    http_method_names = ["get", "head", "options"]

    def get(self, request, pk, *args, **kwargs):
        fetcher = get_object_or_404(PriceFetcher, pk=pk)
        success, result = fetcher.run()
        if not success:
            assert isinstance(result, str)
            messages.error(request, result)
        url = "{}?tab=prices".format(
            reverse_lazy("stocks:stocks", args=[fetcher.stock.pk])
        )
        return HttpResponseRedirect(url)


###
# Bank: Detail, Add, Edit, Delete
###
class BankView(GetUserMixin, TabContextMixin, generic.DetailView):
    template_name = "stocks/bank.j2"
    model = Bank
    object: Bank

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["flows"] = Flow.objects.filter(bank=self.object)
        context["stats"] = self.object.get_stats()
        context["trades"] = Trade.objects.filter(bank=self.object)
        context["dividends"] = self.object.dividends.all()
        return context


class AddBankView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotMixin,
    AjaxResponseMixin,
    generic.CreateView,
):
    form_class = BankForm
    model = Bank
    template_name = "symbols/form_snippet.j2"


class EditBankView(
    GetUserMixin, GetDepotMixin, GetFormWithDepotMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Bank
    form_class = BankForm
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return Bank.objects.filter(depot__in=self.get_user().stock_depots.all())


class DeleteBankView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotMixin,
    AjaxResponseMixin,
    generic.FormView,
):
    model = Bank
    template_name = "symbols/form_snippet.j2"
    form_class = BankSelectForm

    def form_valid(self, form):
        bank = form.cleaned_data["bank"]
        bank.delete()
        return HttpResponse(
            json.dumps({"valid": True}), content_type="application/json"
        )


###
# Flow: Add, Edit, Delete
###
class AddFlowView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotAndInitialDataMixin,
    AjaxResponseMixin,
    generic.CreateView,
):
    model = Flow
    form_class = FlowForm
    template_name = "symbols/form_snippet.j2"


class EditFlowView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotMixin,
    AjaxResponseMixin,
    generic.UpdateView,
):
    model = Flow
    form_class = FlowForm
    template_name = "symbols/form_snippet.j2"


class DeleteFlowView(GetUserMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Flow
    template_name = "symbols/delete_snippet.j2"

    def get_queryset(self):
        return Flow.objects.filter(
            bank__in=Bank.objects.filter(
                depot=self.get_user().get_active_stocks_depot()
            )
        )


###
# Dividend: Add, Edit, Delete
###
class AddDividendView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotAndInitialDataMixin,
    AjaxResponseMixin,
    generic.CreateView,
):
    model = Dividend
    form_class = DividendForm
    template_name = "symbols/form_snippet.j2"


class EditDividendView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotMixin,
    AjaxResponseMixin,
    generic.UpdateView,
):
    model = Dividend
    form_class = DividendForm
    template_name = "symbols/form_snippet.j2"


class DeleteDividendView(GetUserMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Dividend
    template_name = "symbols/delete_snippet.j2"

    def get_queryset(self):
        return Dividend.objects.filter(
            bank__in=Bank.objects.filter(
                depot=self.get_user().get_active_stocks_depot()
            )
        )


###
# Trade: Add, Edit, Delete
###
class AddTradeView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotAndInitialDataMixin,
    AjaxResponseMixin,
    generic.CreateView,
):
    model = Trade
    form_class = TradeForm
    template_name = "symbols/form_snippet.j2"


class EditTradeView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotMixin,
    AjaxResponseMixin,
    generic.UpdateView,
):
    model = Trade
    form_class = TradeForm
    template_name = "symbols/form_snippet.j2"


class DeleteTradeView(GetUserMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Trade
    template_name = "symbols/delete_snippet.j2"

    def get_queryset(self):
        return Trade.objects.filter(
            bank__in=Bank.objects.filter(
                depot=self.get_user().get_active_stocks_depot()
            )
        )
