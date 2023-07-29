from django.contrib.auth.mixins import LoginRequiredMixin
from apps.crypto.models import Asset, Account, Depot, Price, Trade, Transaction, Flow
from django.shortcuts import get_object_or_404
from apps.core.mixins import TabContextMixin
from django.views import generic
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy


class IndexView(LoginRequiredMixin, TabContextMixin, generic.DetailView):
    template_name = 'crypto/index.j2'
    model = Depot

    def get_queryset(self):
        return self.request.user.crypto_depots.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = self.object.get_stats()
        context['assets'] = self.object.assets.order_by('symbol')
        context['accounts'] = self.object.accounts.order_by('name')
        context['trades'] = Trade.objects.filter(account__in=self.object.accounts.all()) \
            .select_related('account', 'buy_asset', 'sell_asset')
        context['transactions'] = Transaction.objects.filter(asset__in=self.object.assets.all()) \
            .select_related('from_account', 'to_account', 'asset')
        context['flows'] = Flow.objects.filter(account__in=self.object.accounts.all()).order_by('-date')
        return context


class AccountView(LoginRequiredMixin, TabContextMixin, generic.DetailView):
    template_name = "crypto/account.j2"
    model = Account

    def get_queryset(self):
        return Account.objects.filter(depot__in=self.request.user.crypto_depots.all())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = self.object.get_stats()
        context['assets'] = self.object.depot.assets.prefetch_related('account_stats').order_by('symbol')
        context["trades"] = self.object.trades.order_by("-date") \
            .select_related("account", "buy_asset", "sell_asset")
        to_transactions = self.object.to_transactions.all()
        from_transactions = self.object.from_transactions.all()
        context["transactions"] = (to_transactions | from_transactions).order_by("-date") \
            .select_related("from_account", "to_account", "asset")
        context['flows'] = Flow.objects.filter(account=self.object).order_by('-date')
        return context


class AssetView(LoginRequiredMixin, TabContextMixin, generic.DetailView):
    template_name = "crypto/asset.j2"
    model = Asset

    def get_queryset(self):
        return Asset.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = self.object.get_stats()
        context["prices"] = Price.objects.filter(symbol=self.object.symbol).order_by("-date")
        accounts = Account.objects.filter(depot=self.request.user.get_active_crypto_depot())
        buy_trades = self.object.buy_trades.filter(account__in=accounts)
        sell_trades = self.object.sell_trades.filter(account__in=accounts)
        context["trades"] = (buy_trades | sell_trades).order_by("-date") \
            .select_related("account", "buy_asset", "sell_asset")
        context["transactions"] = self.object.transactions.filter(from_account__in=accounts).order_by("-date") \
            .select_related("from_account", "to_account", "asset")
        context["fetchers"] = self.object.price_fetchers.all()
        return context


def reset_depot_stats(request, pk, *args, **kwargs):
    depot = get_object_or_404(request.user.crypto_depots.all(), pk=pk)
    depot.reset_all()
    return HttpResponseRedirect(reverse_lazy("crypto:index", args=[depot.pk]))
