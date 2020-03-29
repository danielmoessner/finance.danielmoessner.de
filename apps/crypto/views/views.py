from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from apps.crypto.models import Asset, Account, Depot
from apps.crypto.tasks import update_movies_task
from apps.core.views import TabContextMixin


class IndexView(LoginRequiredMixin, TabContextMixin, generic.DetailView):
    template_name = 'crypto/index.j2'
    model = Depot

    def get_queryset(self):
        return self.request.user.crypto_depots.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = {}
        context['assets'] = self.object.assets.order_by('symbol')
        context['accounts'] = self.object.accounts.order_by('name')
        return context


class AccountView(LoginRequiredMixin, TabContextMixin, generic.DetailView):
    template_name = "crypto/account.j2"
    model = Account

    def get_queryset(self):
        return Account.objects.filter(depot__in=self.request.user.crypto_depots.all())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = {}
        context['assets'] = self.object.depot.assets.order_by('symbol')
        context["trades"] = self.object.trades.order_by("-date")\
            .select_related("account", "buy_asset", "sell_asset", "fees_asset")
        to_transactions = self.object.to_transactions.all()
        from_transactions = self.object.from_transactions.all()
        context["transactions"] = (to_transactions | from_transactions).order_by("-date")\
            .select_related("from_account", "to_account", "asset")
        return context


class AssetView(LoginRequiredMixin, TabContextMixin, generic.DetailView):
    template_name = "crypto/asset.j2"
    model = Asset

    def get_queryset(self):
        return Asset.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = {}
        context["prices"] = self.object.prices.order_by("-date")
        accounts = Account.objects.filter(depot=self.request.user.get_active_crypto_depot_pk())
        buy_trades = self.object.buy_trades.filter(account__in=accounts)
        sell_trades = self.object.sell_trades.filter(account__in=accounts)
        context["trades"] = (buy_trades | sell_trades).order_by("-date")\
            .select_related("account", "buy_asset", "sell_asset", "fees_asset")
        context["transactions"] = self.object.transactions.filter(from_account__in=accounts).order_by("-date")\
            .select_related("from_account", "to_account", "asset")
        return context


def update_movies(request, *args, **kwargs):
    if settings.DEBUG:
        depot = request.user.crypto_depots.get(is_active=True)
        depot.update_movies()
    else:
        depot_pk = request.user.crypto_depots.get(is_active=True).pk
        update_movies_task(depot_pk)
    return HttpResponseRedirect(reverse_lazy("crypto:index"))


def reset_movies(request, *args, **kwargs):
    depot = request.user.crypto_depots.get(is_active=True)
    depot.reset_movies(delete=True)
    return HttpResponseRedirect(reverse_lazy("crypto:index"))
