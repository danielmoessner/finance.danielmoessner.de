from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.views import generic
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from apps.crypto.models import Asset, Account, Depot
from apps.crypto.tasks import update_movies_task
from apps.core.utils import create_paginator
from apps.core.views import TabContextMixin

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from background_task.models import Task
from rest_framework.views import APIView
import json


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


# functions
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


# api
def json_data(pi, g=True, p=True, v=True, cr=True, twr=True, cs=True):
    labels = pi["d"]

    datasets = list()
    if g:
        data_profit = dict()
        data_profit["label"] = "Profit"
        data_profit["data"] = pi["g"]
        data_profit["yAxisID"] = "value"
        datasets.append(data_profit)
    if p:
        data_price = dict()
        data_price["label"] = "Price"
        data_price["data"] = pi["p"]
        data_price["yAxisID"] = "value"
        datasets.append(data_price)
    if v:
        data_value = dict()
        data_value["label"] = "Value"
        data_value["data"] = pi["v"]
        data_value["yAxisID"] = "value"
        datasets.append(data_value)
    if cr:
        data_cr = dict()
        data_cr["label"] = "Current return"
        data_cr["data"] = map(lambda x: x * 100, pi["cr"])
        data_cr["yAxisID"] = "yield"
        datasets.append(data_cr)
    if twr:
        data_twr = dict()
        data_twr["label"] = "True time weighted return"
        data_twr["data"] = map(lambda x: x * 100, pi["twr"])
        data_twr["yAxisID"] = "yield"
        datasets.append(data_twr)
    if cs:
        data_cs = dict()
        data_cs["label"] = "Invested Capital"
        data_cs["data"] = pi["cs"]
        data_cs["yAxisID"] = "value"
        datasets.append(data_cs)
    data = dict()
    data["labels"] = labels
    data["datasets"] = datasets
    return Response(data)


class IndexData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        user = request.user
        try:
            depot = user.crypto_depots.get(is_active=True)
        except Depot.DoesNotExist:
            depot = user.crypto_depots.first()
        timespan = depot.timespans.get(is_active=True)
        pi = depot.get_movie().get_data(timespan)
        return json_data(pi, p=False)


class AccountData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, slug, format=None):
        user = request.user
        try:
            depot = user.crypto_depots.get(is_active=True)
        except Depot.DoesNotExist:
            depot = user.crypto_depots.first()
        account = depot.accounts.get(slug=slug)
        assets = depot.assets.exclude(symbol=user.get_currency_display())
        movies = depot.movies.filter(account=account, asset__in=assets).select_related("asset")
        datasets = list()
        labels = list()
        data = list()
        for movie in movies:
            try:
                value = movie.pictures.latest("d").v
            except ObjectDoesNotExist:
                continue
            if round(value, 2) != 0.00:
                labels.append(str(movie.asset))
                data.append(value)
        data_and_labels = list(sorted(zip(data, labels)))
        labels = [l for d, l in data_and_labels]
        data = [abs(d) for d, l in data_and_labels]
        datasets_data = dict()
        datasets_data["data"] = data
        datasets.append(datasets_data)

        data = dict()
        data["datasets"] = datasets
        data["labels"] = labels
        return Response(data)


class AssetsData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        user = request.user
        try:
            depot = user.crypto_depots.get(is_active=True)
        except Depot.DoesNotExist:
            depot = user.crypto_depots.first()
        assets = depot.assets.exclude(symbol=user.get_currency_display())
        movies = depot.movies.filter(account=None, asset__in=assets).select_related("asset")
        datasets = list()
        labels = list()
        data = list()
        for movie in movies:
            try:
                picture = movie.pictures.latest("d")
            except ObjectDoesNotExist:
                continue
            value = picture.v
            if value and round(value, 2) != 0.00:
                labels.append(str(movie.asset))
                data.append(value)
        data_and_labels = list(sorted(zip(data, labels)))
        labels = [l for d, l in data_and_labels]
        data = [abs(d) for d, l in data_and_labels]
        datasets_data = dict()
        datasets_data["data"] = data
        datasets.append(datasets_data)

        data = dict()
        data["datasets"] = datasets
        data["labels"] = labels
        return Response(data)


class AssetData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, slug, format=None):
        user = request.user
        try:
            depot = user.crypto_depots.get(is_active=True)
        except Depot.DoesNotExist:
            depot = user.crypto_depots.first()
        asset = Asset.objects.get(slug=slug)
        timespan = depot.timespans.get(is_active=True)
        pi = asset.get_movie(depot).get_data(timespan)
        return json_data(pi, twr=False)
