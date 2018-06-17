from django.views import generic
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from finance.crypto.views.views import AccountView
from finance.crypto.views.views import IndexView
from finance.crypto.views.views import AssetView
from finance.core.views.views import CustomDeleteView
from finance.crypto.models import Transaction
from finance.crypto.models import Timespan
from finance.crypto.models import Account
from finance.crypto.models import Asset
from finance.crypto.models import Trade
from finance.crypto.models import Price
from finance.crypto.forms import UpdateActiveOnTimespanForm
from finance.crypto.forms import UpdateTransactionForm
from finance.crypto.forms import CreateTransactionForm
from finance.crypto.forms import CreateTimespanForm
from finance.crypto.forms import UpdateAccountForm
from finance.crypto.forms import CreateAccountForm
from finance.crypto.forms import CreateTradeForm
from finance.crypto.forms import UpdateTradeForm
from finance.crypto.forms import CreatePriceForm
from finance.crypto.forms import CreateAssetForm
from finance.crypto.forms import UpdateAssetForm
from finance.core.utils import form_invalid_universal


# ACCOUNT
class IndexCreateAccountView(IndexView, generic.CreateView):
    form_class = CreateAccountForm
    model = Account

    def form_valid(self, form):
        account = form.save(commit=False)
        account.depot = self.request.user.crypto_depots.get(is_active=True)
        account.save()
        success_url = reverse_lazy("crypto:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="Account could not be created.")


class IndexUpdateAccountView(IndexView):
    def post(self, request, *args, **kwargs):
        form = UpdateAccountForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        account_pk = form.cleaned_data["pk"]
        account = Account.objects.get(pk=account_pk)
        account.name = form.cleaned_data["name"]
        account.save()
        success_url = reverse_lazy("crypto:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors", heading="Account could not be edited.")


class IndexDeleteAccountView(IndexView, CustomDeleteView):
    def form_valid(self, form):
        account_pk = form.cleaned_data["pk"]
        account = Account.objects.get(pk=account_pk)
        account.delete()
        success_url = reverse_lazy("crypto:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, **kwargs):
        return form_invalid_universal(self, form, "errors",
                                      heading="Account could not be deleted.", **kwargs)


# ASSET
class IndexCreateAssetView(IndexView, generic.CreateView):
    form_class = CreateAssetForm
    model = Asset

    def form_valid(self, form):
        asset = form.save(commit=False)
        asset.depot = self.request.user.crypto_depots.get(is_active=True)
        asset.save()
        success_url = reverse_lazy("crypto:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="Asset could not be created.")


class IndexUpdateAssetView(IndexView):
    def post(self, request, *args, **kwargs):
        form = UpdateAssetForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        asset = form.save(commit=False)
        asset.pk = form.cleaned_data["pk"]
        asset.depot = self.request.user.crypto_depots.get(is_active=True)
        asset.save()
        success_url = reverse_lazy("crypto:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="Asset could not be edited.")


class IndexDeleteAssetView(IndexView, CustomDeleteView):
    def form_valid(self, form):
        asset_pk = form.cleaned_data["pk"]
        asset = Asset.objects.get(pk=asset_pk)
        asset.delete()
        success_url = reverse_lazy("crypto:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, **kwargs):
        return form_invalid_universal(self, form, "errors",
                                      heading="Asset could not be deleted.", **kwargs)


# TRADE
class IndexCreateTradeView(IndexView, generic.CreateView):
    form_class = CreateTradeForm
    model = Trade

    def form_valid(self, form):
        trade = form.save()
        success_url = reverse_lazy("crypto:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors", heading="Trade could not be created.")


class AccountCreateTradeView(AccountView, generic.CreateView):
    form_class = CreateTradeForm
    model = Trade

    def form_valid(self, form):
        trade = form.save()
        account = trade.account
        success_url = reverse_lazy("crypto:account", args=[self.request.user.slug, account.slug])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors", heading="Trade could not be created.")


class AccountUpdateTradeView(AccountView):
    def post(self, request, *args, **kwargs):
        form = UpdateTradeForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form, **kwargs)

    def form_valid(self, form):
        trade = form.save(commit=False)
        trade.pk = form.cleaned_data["pk"]
        trade.save()
        account = trade.account
        success_url = reverse_lazy("crypto:account", args=[self.request.user.slug, account.slug])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, **kwargs):
        return form_invalid_universal(self, form, "errors",
                                      heading="Trade could not be edited.", **kwargs)


class AccountDeleteTradeView(AccountView, CustomDeleteView):
    def form_valid(self, form):
        trade_pk = form.cleaned_data["pk"]
        trade = Trade.objects.get(pk=trade_pk)
        account = trade.account
        trade.delete()
        success_url = reverse_lazy("crypto:account", args=[self.request.user.slug, account.slug])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, **kwargs):
        return form_invalid_universal(self, form, "errors",
                                      heading="Trade could not be deleted.", **kwargs)


# TRANSACTION
class AccountCreateTransactionView(AccountView, generic.CreateView):
    form_class = CreateTransactionForm
    model = Transaction

    def form_valid(self, form):
        transaction = form.save()
        account = transaction.from_account
        success_url = reverse_lazy("crypto:account", args=[self.request.user.slug, account.slug])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, **kwargs):
        return form_invalid_universal(self, form, "errors",
                                      heading="Transaction could not be created.", **kwargs)


class AccountUpdateTransactionView(AccountView):
    def post(self, request, *args, **kwargs):
        form = UpdateTransactionForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form, **kwargs)

    def form_valid(self, form):
        transaction = form.save(commit=False)
        transaction.pk = form.cleaned_data["pk"]
        transaction.save()
        url = self.request.META['PATH_INFO']
        success_url = "/".join(url.split("/")[:-2])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, **kwargs):
        return form_invalid_universal(self, form, "errors",
                                      heading="Transaction could not be edited.", **kwargs)


class AccountDeleteTransactionView(AccountView, CustomDeleteView):
    def form_valid(self, form):
        transaction_pk = form.cleaned_data["pk"]
        transaction = Transaction.objects.get(pk=transaction_pk)
        transaction.delete()
        url = self.request.META['PATH_INFO']
        success_url = "/".join(url.split("/")[:-2])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, **kwargs):
        return form_invalid_universal(self, form, "errors",
                                      heading="Transaction could not be deleted.", **kwargs)


# PRICE
class AssetCreatePriceView(AssetView, generic.CreateView):
    form_class = CreatePriceForm
    model = Price

    def form_valid(self, form):
        price = form.save(commit=False)
        asset = Asset.objects.get(slug=self.request.kwargs["slug"])
        price.asset = asset
        price.currency = self.request.user.currency
        price.save()
        success_url = reverse_lazy("crypto:asset", args=[self.request.user.slug, asset.slug])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors", heading="Price could not be created.")


class AssetDeletePriceView(AssetView, CustomDeleteView):
    def form_valid(self, form):
        price_pk = form.cleaned_data["pk"]
        price = Price.objects.get(pk=price_pk)
        asset = price.asset
        price.delete()
        success_url = reverse_lazy("crypto:asset", args=[self.request.user.slug, asset.slug])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, **kwargs):
        return form_invalid_universal(self, form, "errors",
                                      heading="Change could not be deleted.", **kwargs)


# TIMESPAN
class IndexCreateTimespanView(IndexView, generic.CreateView):
    form_class = CreateTimespanForm
    model = Timespan

    def form_valid(self, form):
        timespan = form.save(commit=False)
        timespan.depot = self.request.user.crypto_depots.get(is_active=True)
        timespan.is_active = False
        timespan.save()
        success_url = reverse_lazy("crypto:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="Timespan could not be created.")


class IndexUpdateActiveOnTimespanView(IndexView):
    def post(self, request, *args, **kwargs):
        form = UpdateActiveOnTimespanForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.request.user.crypto_depots.get(is_active=True).timespans.update(is_active=False)
        timespan_pk = form.cleaned_data["pk"]
        Timespan.objects.filter(pk=timespan_pk).update(is_active=True)
        success_url = reverse_lazy("crypto:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="Timespan could not be created.")


class IndexDeleteTimespanView(IndexView, CustomDeleteView):
    def form_valid(self, form):
        timespan_pk = form.cleaned_data["pk"]
        timespan = Timespan.objects.get(pk=timespan_pk)
        if timespan.is_active:
            form_invalid_universal(self, form, "errors",
                                   heading="Timespan could not be deleted, because it's still "
                                           "active.",
                                   **self.request.kwargs)
        timespan.delete()
        success_url = reverse_lazy("crypto:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, **kwargs):
        return form_invalid_universal(self, form, "errors",
                                      heading="Timespan could not be deleted.", **kwargs)
