from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic

from finance.crypto.models import Account
from finance.crypto.models import Asset
from finance.crypto.models import Depot
from finance.crypto.models import Movie

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime
from decimal import Decimal
import pytz


# VIEWS
class IndexView(generic.TemplateView):
    template_name = "crypto_index.njk"

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        context["depot"] = context["user"].crypto_depots.get(is_active=True)
        context["accounts"] = context["depot"].accounts.order_by("name")
        movies = context["depot"].movies.filter(
            account__in=context["accounts"], asset=None).order_by("account__name")
        assert len(context["accounts"]) == len(movies)
        context["accounts_movies"] = zip(context["accounts"], movies)
        context["assets_all"] = context["depot"].assets.order_by("name")
        assets = context["assets_all"].exclude(
            symbol=context["user"].get_currency_display()).order_by("name")
        movies = context["depot"].movies.filter(asset__in=assets, account=None).order_by(
            "asset__name")
        assert len(assets) == len(movies)
        context["assets_movies"] = zip(assets, movies)
        context["timespans"] = context["depot"].timespans.all()

        context["movie"] = context["depot"].movies.get(account=None, asset=None)
        return context


class AccountView(generic.TemplateView):
    template_name = "crypto_account.njk"

    def get_context_data(self, **kwargs):
        context = {"user": self.request.user}
        context["depot"] = context["user"].crypto_depots.get(is_active=True)
        context["accounts"] = context["depot"].accounts.all()
        context["assets_all"] = context["depot"].assets.order_by("name")
        context["timespans"] = context["depot"].timespans.all()
        context["account"] = context["depot"].accounts.get(slug=kwargs["slug"])
        assets = context["assets_all"].exclude(
            symbol=context["user"].get_currency_display()).order_by("name")
        movies = context["account"].movies.filter(asset__in=assets).order_by("asset__name")
        assert len(assets) == len(movies)
        context["assets_movies"] = zip(assets, movies)
        context["trades"] = context["account"].trades.order_by("-date").select_related(
            "account", "buy_asset", "sell_asset", "fees_asset")
        to_transactions = context["account"].to_transactions.all()
        from_transactions = context["account"].from_transactions.all()
        context["transactions"] = (to_transactions | from_transactions).order_by(
            "-date").select_related("from_account", "to_account", "asset")
        context["movie"] = context["depot"].movies.get(account=context["account"], asset=None)
        return context


class AssetView(generic.TemplateView):
    template_name = "crypto_asset.njk"

    def get_context_data(self, **kwargs):
        context = super(AssetView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        context["depot"] = context["user"].crypto_depots.get(is_active=True)
        context["accounts"] = context["depot"].accounts.all()
        context["assets_all"] = context["depot"].assets.order_by("name")
        context["assets"] = context["assets_all"].exclude(
            symbol=context["user"].get_currency_display()).order_by("name")
        context["timespans"] = context["depot"].timespans.all()

        context["asset"] = Asset.objects.get(slug=kwargs["slug"])
        context["prices"] = context["asset"].prices.order_by("-date")
        buy_trades = context["asset"].buy_trades.all()
        sell_trades = context["asset"].sell_trades.all()
        context["trades"] = (buy_trades | sell_trades).order_by("-date").select_related(
            "account", "buy_asset", "sell_asset", "fees_asset")
        context["transactions"] = context["asset"].transactions.order_by("-date").select_related(
            "from_account", "to_account", "asset")
        context["movie"] = context["depot"].movies.get(account=None, asset=context["asset"])
        return context


# FUNCTIONS
def move_asset(request, *args, **kwargs):
    if request.method == "POST":
        if all(k in request.POST for k in ("from_account", "asset", "to_account", "fees", "date",
                                           "amount")):
            from_account = Account.objects.get(pk=request.POST["from_account"])
            to_account = Account.objects.get(pk=request.POST["to_account"])
            asset = Asset.objects.get(pk=request.POST["asset"])
            tx_fees = Decimal(request.POST["fees"])
            date = datetime.strptime(request.POST["date"], '%Y-%m-%dT%H:%M')\
                .replace(tzinfo=pytz.utc)
            amount = Decimal(request.POST["amount"])
            asset.move(date, from_account, amount, to_account, tx_fees)
            return HttpResponseRedirect(
                reverse_lazy("crypto:account", args=[request.user.slug, from_account.slug, ]))
        else:
            pass  # error correction


def update_prices(request, *args, **kwargs):
    depot = Depot.objects.get(name="CMain")
    depot.update_prices()
    return HttpResponseRedirect(reverse_lazy("crypto:index", args=[request.user.slug, ]))


def update_movies(request, *args, **kwargs):
    depot = request.user.crypto_depots.get(is_active=True)
    Movie.update_all(depot, force_update=True)
    return HttpResponseRedirect(reverse_lazy("crypto:index", args=[request.user.slug, ]))


# API DATA
def json_data(pi, g=True, p=True, v=True, cr=True, ttwr=True, cs=True):
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
        data_cr["data"] = pi["cr"]
        data_cr["yAxisID"] = "yield"
        datasets.append(data_cr)
    if ttwr:
        data_ttwr = dict()
        data_ttwr["label"] = "True time weighted return"
        data_ttwr["data"] = pi["ttwr"]
        data_ttwr["yAxisID"] = "yield"
        datasets.append(data_ttwr)
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

    def get(self, request, user_slug, format=None):
        user = request.user
        depot = user.crypto_depots.get(is_active=True)
        timespan = depot.timespans.get(is_active=True)
        pi = depot.get_movie().get_data(timespan)
        return json_data(pi, p=False)


class AccountData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, user_slug, slug, format=None):
        user = request.user
        depot = user.crypto_depots.get(is_active=True)
        timespan = depot.timespans.get(is_active=True)
        account = depot.accounts.get(slug=slug)
        assets = depot.assets.exclude(symbol=user.get_currency_display())
        movies = depot.movies.filter(account=account, asset__in=assets).select_related("asset")
        datasets = list()
        labels = list()
        data = list()
        for movie in movies:
            value = movie.get_values(user, ["v", ], timespan)["v"]
            if value != "x" and round(value, 2) != 0.00:
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

    def get(self, request, user_slug, format=None):
        user = request.user
        depot = user.crypto_depots.get(is_active=True)
        timespan = depot.timespans.get(is_active=True)
        assets = depot.assets.exclude(symbol=user.get_currency_display())
        movies = depot.movies.filter(account=None, asset__in=assets).select_related("asset")
        datasets = list()
        labels = list()
        data = list()
        for movie in movies:
            value = movie.get_values(user, ["v", ], timespan)["v"]
            if value != "x" and round(value, 2) != 0.00:
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

    def get(self, request, user_slug, slug, format=None):
        user = request.user
        depot = user.crypto_depots.get(is_active=True)
        asset = Asset.objects.get(slug=slug)
        timespan = depot.timespans.get(is_active=True)
        pi = asset.get_movie().get_data(timespan)
        return json_data(pi, ttwr=False)
