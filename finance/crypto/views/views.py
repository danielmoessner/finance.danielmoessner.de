from django.contrib import messages
from django.views import generic
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from finance.crypto.models import Asset
from finance.crypto.tasks import update_movies_task


from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from background_task.models import Task
from rest_framework.views import APIView
import json


# messenger
def messenger(request):
    if request.user.crypto_depots.get(is_active=True).movies.exclude(
            asset__symbol=request.user.currency).filter(update_needed=True).exists():
        hit = False
        tasks = Task.objects.filter(task_name="finance.crypto.tasks.update_movies_task")
        for task in tasks:
            depot_pk = json.loads(task.task_params)[0][0]
            if depot_pk == request.user.crypto_depots.get(is_active=True).pk:
                text = "One update is scheduled. You will be notified as soon as it succeeded."
                messages.info(request, text)
                hit = True
        if not hit:
            text = "New data is available. Hit the update button so that I can update everything."
            messages.info(request, text)
    else:
        text = "Everything is up to date."
        messages.success(request, text)


# VIEWS
class IndexView(generic.TemplateView):
    template_name = "crypto_index.njk"

    def get_context_data(self, **kwargs):
        messenger(self.request)
        # general
        context = dict(user=self.request.user)
        context["depot"] = context["user"].crypto_depots.get(is_active=True)
        context["timespans"] = context["depot"].timespans.all()
        context["timespan"] = context["depot"].timespans.get(is_active=True)
        print(context["timespan"].start_date)
        # accounts
        context["accounts"] = context["depot"].accounts.order_by("name")
        account_movies = context["depot"].movies.filter(
            account__in=context["accounts"], asset=None).order_by("account__name")
        context["accounts_movies"] = zip(context["accounts"], account_movies)
        # assets
        context["assets"] = context["depot"].assets.order_by("symbol", "private_name")
        context["private_assets"] = context["assets"].exclude(private_symbol=None)
        context["public_assets"] = context["assets"].exclude(symbol=None)
        context["asset_symbol_choices"] = Asset.SYMBOL_CHOICES
        asset_movies = context["depot"].movies.filter(asset__in=context["assets"], account=None)\
            .order_by("asset__symbol", "asset__private_symbol")
        context["assets_movies"] = zip(context["assets"], asset_movies)
        # movie
        context["movie"] = context["depot"].movies.get(account=None, asset=None)
        # error
        if (not len(context["assets"]) == len(asset_movies)) or \
                (not len(context["accounts"]) == len(account_movies)):
            context["depot"].get_movie().update_all(disable_update=True)
            context = self.get_context_data(**kwargs)
        # return
        return context


class AccountView(generic.TemplateView):
    template_name = "crypto_account.njk"

    def get_context_data(self, **kwargs):
        messenger(self.request)
        # general
        context = dict(user=self.request.user)
        context["depot"] = context["user"].crypto_depots.get(is_active=True)
        context["timespans"] = context["depot"].timespans.all()
        context["timespan"] = context["depot"].timespans.get(is_active=True)
        # account(s)
        context["accounts"] = context["depot"].accounts.all()
        context["account"] = context["accounts"].get(slug=kwargs["slug"])
        # assets
        context["assets"] = context["depot"].assets.order_by("symbol", "private_name")
        context["private_assets"] = context["assets"].exclude(private_symbol=None)
        context["public_assets"] = context["assets"].exclude(symbol=None)
        context["asset_symbol_choices"] = Asset.SYMBOL_CHOICES
        asset_movies = context["depot"].movies.filter(asset__in=context["assets"], account=None) \
            .order_by("asset__symbol", "asset__private_symbol")
        context["assets_movies"] = zip(context["assets"], asset_movies)
        # trades
        context["trades"] = context["account"].trades.order_by("-date").select_related(
            "account", "buy_asset", "sell_asset", "fees_asset")
        # transactions
        to_transactions = context["account"].to_transactions.all()
        from_transactions = context["account"].from_transactions.all()
        context["transactions"] = (to_transactions | from_transactions).order_by(
            "-date").select_related("from_account", "to_account", "asset")
        # movie
        context["movie"] = context["depot"].movies.get(account=context["account"], asset=None)
        # error
        if not len(context["assets"]) == len(asset_movies):
            context["depot"].get_movie().update_all(disable_update=True)
            context = self.get_context_data(**kwargs)
        # return
        return context


class AssetView(generic.TemplateView):
    template_name = "crypto_asset.njk"

    def get_context_data(self, **kwargs):
        messenger(self.request)
        # general
        context = dict(user=self.request.user)
        context["depot"] = context["user"].crypto_depots.get(is_active=True)
        context["timespans"] = context["depot"].timespans.all()
        context["timespan"] = context["depot"].timespans.get(is_active=True)
        # account
        context["accounts"] = context["depot"].accounts.all()
        # asset(s)
        context["assets"] = context["depot"].assets.order_by("symbol", "private_name")
        context["asset"] = context["assets"].get(slug=kwargs["slug"])
        # prices
        context["prices"] = context["asset"].prices.order_by("-date")
        # trades
        buy_trades = context["asset"].buy_trades.all()
        sell_trades = context["asset"].sell_trades.all()
        context["trades"] = (buy_trades | sell_trades).order_by("-date").select_related(
            "account", "buy_asset", "sell_asset", "fees_asset")
        # transactions
        context["transactions"] = context["asset"].transactions.order_by("-date").select_related(
            "from_account", "to_account", "asset")
        # movie
        context["movie"] = context["depot"].movies.get(account=None, asset=context["asset"])
        # return
        return context


# FUNCTIONS
def update_movies(request, *args, **kwargs):
    depot_pk = request.user.crypto_depots.get(is_active=True).pk
    update_movies_task(depot_pk)
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
        # timespan = depot.timespans.get(is_active=True)
        account = depot.accounts.get(slug=slug)
        assets = depot.assets.exclude(symbol=user.get_currency_display())
        movies = depot.movies.filter(account=account, asset__in=assets).select_related("asset")
        datasets = list()
        labels = list()
        data = list()
        for movie in movies:
            value = movie.get_values(user, ["v"])["v"]
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
        pi = asset.get_movie(depot).get_data(timespan)
        return json_data(pi, ttwr=False)
