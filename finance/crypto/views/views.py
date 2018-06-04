from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic

from finance.crypto.models import Account
from finance.crypto.models import Asset
from finance.crypto.models import Trade
from finance.crypto.models import Price
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
class CryptoView(generic.TemplateView):
    template_name = "crypto_index.njk"

    def get_context_data(self, **kwargs):
        context = super(CryptoView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        context["depot"] = context["user"].crypto_depots.get(is_active=True)
        context["accounts"] = context["depot"].accounts.all()
        context["assets"] = Asset.objects.exclude(
            symbol=context["user"].get_currency_display()).order_by("name")
        context["assets_all"] = Asset.objects.order_by("name")

        context["parent_timespans"] = context["user"].crypto_intelligent_timespans.all()
        context["movie"] = context["depot"].movies.get(account=None, asset=None)
        return context


class AccountView(generic.TemplateView):
    template_name = "crypto_account.njk"

    def get_context_data(self, **kwargs):
        context = super(AccountView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        context["depot"] = context["user"].crypto_depots.get(is_active=True)
        context["accounts"] = context["depot"].accounts.all()
        context["assets"] = Asset.objects.exclude(
            symbol=context["user"].get_currency_display()).order_by("name")
        context["assets_all"] = Asset.objects.order_by("name")
        context["parent_timespans"] = context["user"].crypto_intelligent_timespans.all()

        context["account"] = context["depot"].accounts.get(slug=kwargs["slug"])
        context["trades"] = context["account"].trades.order_by("-date")
        context["movie"] = context["depot"].movies.get(account=context["account"], asset=None)
        return context


class AssetView(generic.TemplateView):
    template_name = "crypto_asset.njk"

    def get_context_data(self, **kwargs):
        context = super(AssetView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        context["depot"] = context["user"].crypto_depots.get(is_active=True)
        context["accounts"] = context["depot"].accounts.all()
        context["assets"] = Asset.objects.exclude(
            symbol=context["user"].get_currency_display()).order_by("name")
        context["assets_all"] = Asset.objects.order_by("name")
        context["parent_timespans"] = context["user"].crypto_intelligent_timespans.all()

        context["asset"] = Asset.objects.get(slug=kwargs["slug"])
        context["prices"] = context["asset"].prices.order_by("-date")
        buy_trades = context["asset"].buy_trades.all()
        sell_trades = context["asset"].sell_trades.all()
        context["trades"] = (buy_trades | sell_trades).order_by("-date")
        context["movie"] = context["depot"].movies.get(account=None, asset=context["asset"])
        return context


# FUNCTIONS
def add(request, *args, **kwargs):
    if request.method == "POST":
        if all(k in request.POST for k in ("asset", "date", "price", "currency", "reverse")):
            asset = Asset.objects.get(pk=request.POST["asset"])
            date = datetime.strptime(request.POST["date"], '%Y-%m-%dT%H:%M')\
                .replace(tzinfo=pytz.utc)
            price = Decimal(request.POST["price"])
            currency = str(request.POST["currency"])
            price = Price(asset=asset, date=date, price=price, currency=currency)
            price.save()
            return HttpResponseRedirect(request.POST["reverse"])
        elif all(k in request.POST for k in ("name", "symbol", "reverse")):
            symbol = str(request.POST["symbol"])
            name = str(request.POST["name"])
            asset = Asset(symbol=symbol, name=name)
            asset.save()
            return HttpResponseRedirect(request.POST["reverse"])
        elif all(k in request.POST for k in ("asset", "date", "price", "reverse")):
            asset = Asset.objects.get(pk=request.POST["asset"])
            date = datetime.strptime(request.POST["date"], '%Y-%m-%dT%H:%M')\
                .replace(tzinfo=pytz.utc)
            asset_price = Decimal(request.POST["price"])
            currency = request.user.currency
            price = Price(asset=asset, date=date, price=asset_price, currency=currency)
            price.save()
            return HttpResponseRedirect(request.POST["reverse"])
        elif all(k in request.POST for k in ("name", "depot", "reverse")):
            depot = Depot.objects.get(pk=request.POST["depot"])
            name = str(request.POST["name"])
            account = Account(depot=depot, name=name)
            account.save()
            return HttpResponseRedirect(request.POST["reverse"])
        elif all(k in request.POST for k in ("account", "date", "buy_amount", "buy_asset", "fees",
                                             "fees_asset", "sell_amount", "sell_asset",
                                             "reverse")):
            account = Account.objects.get(pk=request.POST["account"])
            date = datetime.strptime(request.POST["date"], '%Y-%m-%dT%H:%M')\
                .replace(tzinfo=pytz.utc)
            buy_amount = Decimal(request.POST["buy_amount"])
            buy_asset = Asset.objects.get(pk=request.POST["buy_asset"])
            fees = Decimal(request.POST["fees"])
            fees_asset = Asset.objects.get(pk=request.POST["fees_asset"])
            sell_amount = Decimal(request.POST["sell_amount"])
            sell_asset = Asset.objects.get(pk=request.POST["sell_asset"])
            trade = Trade(account=account, date=date, buy_amount=buy_amount, buy_asset=buy_asset,
                          fees=fees,
                          fees_asset=fees_asset, sell_amount=sell_amount, sell_asset=sell_asset)
            trade.save(add_change=True)
            return HttpResponseRedirect(request.POST["reverse"])
        else:
            pass  # error correction
    else:
        raise Exception("Something is wrong here. Why is this no POST request?")


def delete(request, *args, **kwargs):
    if request.method == "POST":
        if "asset" in request.POST:
            asset = Asset.objects.get(pk=request.POST["asset"])
            if asset.get_ca() == 0:
                asset.delete()
            else:
                pass  # error correction
            return HttpResponseRedirect(reverse_lazy("crypto:index", args=[request.user.slug, ]))
        if "price" in request.POST:
            price = Price.objects.get(pk=request.POST["price"])
            price.delete()
            return HttpResponseRedirect(reverse_lazy("crypto:asset",
                                                     args=[request.user.slug, kwargs["slug"], ]))
        if "trade" in request.POST and "reverse" in request.POST:
            trade = Trade.objects.get(pk=request.POST["trade"])
            trade.delete()
            url = request.POST["reverse"]
            return HttpResponseRedirect(url)
        else:
            pass  # error correction
    else:
        raise Exception("Something is wrong here. Why is this no POST request?")


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
    for data in datasets:
        print(list(data["data"])[-3:])
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
        pi = depot.get_movie().get_timespan_data(depot.timespan)
        return json_data(pi, p=False)


class AccountData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, user_slug, slug, format=None):
        user = request.user
        depot = user.crypto_depots.get(is_active=True)
        account = depot.accounts.get(slug=slug)
        pi = account.get_movie().get_timespan_data(depot.timespan)
        return json_data(pi, p=False)


class AssetsData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, user_slug, format=None):
        user = request.user
        depot = user.crypto_depots.get(is_active=True)

        datasets = list()
        labels = list()
        data = list()
        for asset in Asset.objects.exclude(symbol=user.get_currency_display()):
            movie = asset.get_movie(depot)
            labels.append(str(asset))
            data.append(movie.get_timespan_data(depot.timespan)["v"].last()
                        if movie.get_timespan_data(depot.timespan)["v"].last() is not None else 0)
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
        pi = asset.get_movie(depot).get_timespan_data(depot.timespan)
        return json_data(pi)
