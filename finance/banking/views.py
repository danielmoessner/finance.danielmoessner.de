from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic

from finance.core.utils import create_slug
from .models import IntelligentTimespan
from .models import Category
from .models import Account
from .models import Change
from .models import Movie
from .models import Depot

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import timedelta
from datetime import datetime
from decimal import Decimal
import pandas as pd
import pytz


# VIEWS
class IndexView(generic.TemplateView):
    template_name = "banking_index.njk"

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        context["depot"] = context["user"].banking_depots.get(is_active=True)
        context["accounts"] = context["depot"].accounts.order_by("name")
        context["categories"] = context["user"].categories.order_by("name")
        context["parent_timespans"] = context["user"].banking_intelligent_timespans.all()

        context["movie"] = context["depot"].movies.get(account=None, category=None)
        return context


class AccountView(generic.TemplateView):
    template_name = "banking_account.njk"

    def get_context_data(self, **kwargs):
        context = super(AccountView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        context["depot"] = context["user"].banking_depots.get(is_active=True)
        context["accounts"] = context["depot"].accounts.order_by("name")
        context["categories"] = context["user"].categories.order_by("name")
        context["parent_timespans"] = context["user"].banking_intelligent_timespans.all()

        context["account"] = context["depot"].accounts.get(slug=kwargs["slug"])
        context["changes"] = context["account"].changes.order_by("-date", "-pk")
        context["stats"] = context["depot"].movies.get(account=context["account"], category=None)
        return context


class CategoryView(generic.TemplateView):
    template_name = "banking_category.njk"

    def get_context_data(self, **kwargs):
        context = super(CategoryView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        context["depot"] = context["user"].banking_depots.get(is_active=True)
        context["accounts"] = context["depot"].accounts.order_by("name")
        context["categories"] = context["user"].categories.order_by("name")
        context["parent_timespans"] = context["user"].banking_intelligent_timespans.all()

        context["category"] = context["user"].categories.get(slug=kwargs["slug"])
        context["changes"] = context["category"].changes.order_by("-date", "-pk")
        context["stats"] = context["depot"].movies.get(account=None, category=context["category"])
        return context


# FUNCTIONS
def add(request, user_slug):
    if request.method == "POST":
        if all(k in request.POST for k in ("name", "depot", "reverse")):
            depot = Depot.objects.get(pk=request.POST["depot"])
            name = str(request.POST["name"])
            account = Account(depot=depot, name=name)
            account.save()
            return HttpResponseRedirect(request.POST["reverse"])
        elif all(k in request.POST for k in ("name", "start_date", "end_date", "period",
                                             "reverse_lazy")):
            url = request.POST["reverse_lazy"]
            name = str(request.POST["name"])
            start_date = datetime.strptime(request.POST["start_date"], '%Y-%m-%dT%H:%M')\
                .replace(tzinfo=pytz.utc)
            if request.POST["end_date"] != "":
                period = None
                end_date = datetime.strptime(request.POST["start_date"], '%Y-%m-%dT%H:%M')\
                    .replace(tzinfo=pytz.utc)
            elif request.POST["period"] != "":
                period = timedelta(days=int(request.POST["period"]))
                end_date = None
            else:
                return  # error correction
            timespan = IntelligentTimespan(name=name, start_date=start_date, end_date=end_date,
                                           period=period)
            timespan.save()
            return HttpResponseRedirect(url)
        elif all(k in request.POST for k in ("account", "date", "category", "description",
                                             "change", "reverse")):
            account = Account.objects.get(pk=request.POST["account"])
            date = datetime.strptime(request.POST["date"], '%Y-%m-%dT%H:%M')\
                .replace(tzinfo=pytz.utc)
            category = Category.objects.get(pk=request.POST["category"])
            description = str(request.POST["description"])
            change_change = Decimal(request.POST["change"])
            change = Change(account=account, date=date, category=category, description=description,
                            change=change_change)
            change.save()
            return HttpResponseRedirect(request.POST["reverse"])
        elif all(k in request.POST for k in ("name", "description", "reverse")):
            name = str(request.POST["name"])
            description = str(request.POST["description"])
            user = request.user
            category = Category(name=name, description=description, user=user)
            category.save()
            return HttpResponseRedirect(request.POST["reverse"])
        else:
            pass  # error correction
    else:
        raise Exception("Something is wrong here. Why is this no POST request?")


def edit(request, user_slug):
    if request.method == "POST":
        if all(key in request.POST for key in ("category", "description", "name")):
            category = Category.objects.get(pk=request.POST["category"])
            category.description = request.POST["description"]
            category.name = request.POST["name"]
            category.save()
            return HttpResponseRedirect(reverse_lazy("index", args=[request.user.slug, ]))
        elif all(key in request.POST for key in ("account", "name")):
            account = Account.objects.get(pk=request.POST["account"])
            account.name = request.POST["name"]
            account.slug = create_slug(account)
            account.save()
            return HttpResponseRedirect(reverse_lazy("index", args=[request.user.slug, ]))
        elif all(key in request.POST for key in ("account", "change", "date", "category",
                                                 "description",
                                                 "change_change", "reverse")):
            url = request.POST["reverse"]
            change = Change.objects.get(pk=request.POST["change"])
            change.account = Account.objects.get(pk=request.POST["account"])
            change.date = datetime.strptime(request.POST["date"], '%Y-%m-%dT%H:%M')\
                .replace(tzinfo=pytz.utc)
            change.category = Category.objects.get(pk=request.POST["category"])
            change.description = request.POST["description"]
            change.change = Decimal(request.POST["change_change"])
            change.save()
            return HttpResponseRedirect(url)
        else:
            pass  # error correction
    else:
        raise Exception("Something is wrong here. Why is this no POST request?")


def delete(request, user_slug):
    if request.method == "POST":
        if "category" in request.POST:
            category = Category.objects.get(pk=request.POST["category"])
            category.delete()
            return HttpResponseRedirect(reverse_lazy("banking:index", args=[request.user.slug, ]))
        elif all(key in request.POST for key in ("account", "reverse")):
            account = Account.objects.get(pk=request.POST["account"])
            account.delete()
            return HttpResponseRedirect(request.POST["reverse"])
        elif all(key in request.POST for key in ("timespan", "reverse")):
            url = request.POST["reverse"]
            pts = IntelligentTimespan.objects.get(pk=request.POST["timespan"])
            pts.delete()
            return HttpResponseRedirect(url)
        elif all(key in request.POST for key in ("change", "reverse")):
            change = Change.objects.get(pk=request.POST["change"])
            change.delete()
            return HttpResponseRedirect(request.POST["reverse"])
        else:
            pass  # error correction
    else:
        raise Exception("Something is wrong here. Why is this no POST request?")


def update_stats(request, user_slug):
    Movie.update_all()
    return HttpResponseRedirect(reverse_lazy("banking:index", args=[request.user.slug, ]))


def set_timespan(request, user_slug):
    if request.method == "POST":
        if all(key in request.POST for key in ("reverse", "timespan", "depot")):
            pts = IntelligentTimespan.objects.get(pk=request.POST["timespan"])
            depot = Depot.objects.get(pk=request.POST["depot"])
            depot.timespan = pts
            depot.save()
            return HttpResponseRedirect(request.POST["reverse"])


def update_timespans(request, user_slug):
    for pts in IntelligentTimespan.objects.all():
        pts.create_timespans()
    return HttpResponseRedirect(reverse_lazy("banking:index", args=[request.user.slug, ]))


# API
class IndexData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, user_slug):
        user = request.user
        depot = Depot.objects.get(user=user, is_active=True)

        df1 = pd.DataFrame()
        depot_movie = depot.get_movie()
        df1["balance"] = depot_movie.get_timespan_data(depot.timespan)["b"]
        df1["dates"] = [date.date() for date in
                        list(depot_movie.get_timespan_data(depot.timespan)["d"])]
        df1.set_index("dates", inplace=True)
        for account in Account.objects.filter(depot=depot):
            account_movie = account.get_movie()
            df2 = pd.DataFrame()
            account_movie = account.get_movie()
            df2[str(account)] = account_movie.get_timespan_data(depot.timespan)["b"]
            df2["dates"] = [date.date() for date in
                            list(account_movie.get_timespan_data(depot.timespan)["d"])]
            df2.set_index("dates", inplace=True)
            df1 = pd.concat([df1, df2], join="outer", ignore_index=False)
            df1.sort_index(inplace=True)
            df1.ffill(inplace=True)
        df1 = df1[~df1.index.duplicated(keep="last")]
        df1.fillna(0, inplace=True)

        datasets = list()
        dataset = dict()
        dataset["label"] = "Total"
        dataset["type"] = "line"
        dataset["data"] = df1["balance"].tolist()
        datasets.append(dataset)
        for column_name in df1.columns.values.tolist():
            if column_name != "balance":
                dataset = dict()
                dataset["label"] = str(column_name)
                dataset["type"] = "line"
                dataset["data"] = df1[column_name].tolist()
                datasets.append(dataset)

        data = dict()
        data["labels"] = df1.index.tolist()
        data["datasets"] = datasets
        return Response(data)


class AccountData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, user_slug, slug, format=None):
        user = request.user
        depot = Depot.objects.get(user=user, is_active=True)

        df1 = pd.DataFrame()
        account = Account.objects.get(slug=slug)
        account_movie = account.get_movie()
        df1["Balance"] = account_movie.get_timespan_data(depot.timespan)["b"]
        df1["dates"] = [date.date() for date in
                        list(account_movie.get_timespan_data(depot.timespan)["d"])]
        df1["index"] = range(len(df1["dates"]))
        df1.set_index("index", inplace=True)
        for category in set([change.category for change in account.changes.all()]):
            account_movie = Movie.objects.get(depot=depot, account=account, category=category)
            # df1 and the data have the same length because of the way the changes are calculated
            # with a account-category movie
            df1[str(category)] = account_movie.get_timespan_data(depot.timespan)["c"]

        deletes = list()
        for i in range(len(df1) - 1):
            if df1.iloc[i]["dates"] == df1.iloc[i+1]["dates"]:
                # The 2 is important, because you don't want to add dates or balances together
                for k in range(2, len(df1.iloc[i])):
                    column_name = df1.iloc[:, k].name
                    df1.at[i+1, column_name] = df1.at[i, column_name] + df1.at[i+1, column_name]
                deletes.append(i)
        df1.drop(deletes, inplace=True)

        df2 = pd.DataFrame(pd.date_range(start=df1["dates"].iloc[0], end=df1["dates"].iloc[-1]),
                           columns=["dates", ])
        df1.set_index("dates", inplace=True)
        df2.set_index("dates", inplace=True)

        df = df1.join(df2, how="outer")
        df["Balance"] = df["Balance"].ffill()
        df.fillna(0, inplace=True)

        datasets = list()
        dataset = dict()
        dataset["label"] = "Balance"
        dataset["type"] = "line"
        dataset["data"] = df["Balance"].tolist()
        datasets.append(dataset)
        for column_name in df.columns.values.tolist():
            if column_name != "Balance":
                dataset = dict()
                dataset["label"] = str(column_name)
                dataset["type"] = "bar"
                dataset["data"] = df[column_name].tolist()
                datasets.append(dataset)

        data = dict()
        data["labels"] = df.index.tolist()
        data["datasets"] = datasets
        return Response(data)


class CategoryData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, user_slug, slug, format=None):
        user = request.user
        depot = Depot.objects.get(user=user, is_active=True)

        category = Category.objects.get(slug=slug)
        movie = Movie.objects.get(depot=depot, account=None, category=category)
        labels = list()
        data = list()

        dates = movie.get_timespan_data(depot.timespan)["d"]
        changes = movie.get_timespan_data(depot.timespan)["c"]
        last_month = None
        changes_sum = 0
        for i in range(len(dates)):
            if last_month is None:
                last_month = dates[i].month
                changes_sum += changes[i]
            else:
                if dates[i].month == last_month:
                    changes_sum += changes[i]
                else:
                    labels.append(str(dates[i - 1].month) + "/" + str(dates[i - 1].year))
                    data.append(changes_sum)
                    last_month = dates[i].month
                    changes_sum = changes[i]
            if i == len(dates) - 1:
                labels.append(str(dates[i].month) + "/" + str(dates[i].year))
                data.append(changes_sum)

        if len(labels) > 0:
            first_year = int(labels[0][3:]) if len(labels[0]) == 7 else int(labels[0][2:])
            first_month = int(labels[0][:2]) if len(labels[0]) == 7 else int(labels[0][:1])
            last_year = int(labels[-1][3:]) if len(labels[-1]) == 7 else int(labels[-1][2:])
            last_month = int(labels[-1][:2]) if len(labels[-1]) == 7 else int(labels[-1][:1])
        else:
            return Response(None)

        dates = list()
        for year in range(first_year, last_year + 1):
            if year == first_year == last_year:
                months = range(first_month, last_month + 1)
            elif year == first_year:
                months = range(first_month, 13)
            elif year == last_year:
                months = range(1, last_month + 1)
            else:
                months = range(1, 13)
            for month in months:
                dates.append(str(month) + "/" + str(year))
        changes = list()
        for i in range(len(dates)):
            changes.append(0)
            for k in range(len(labels)):
                if dates[i] == labels[k]:
                    changes[i] = data[k]
                    break

        dataset = dict()
        dataset["data"] = changes
        dataset["label"] = "Change"
        if len(changes) > 0:
            dataset["backgroundColor"] = "hsla(358, 100%, 50%, 1)" if sum(changes) < 0 \
                else "hsla(140, 100%, 50%, 1)"

        datasets = list()
        datasets.append(dataset)

        data = dict()
        data["datasets"] = datasets
        data["labels"] = dates
        return Response(data)


class CategoriesData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, user_slug):
        user = request.user
        depot = Depot.objects.get(user=user, is_active=True)

        datasets = list()
        labels = list()
        data = list()
        for category in Category.objects.all():
            category_movie = Movie.objects.get(depot=depot, account=None, category=category)
            labels.append(str(category))
            data.append(category_movie.get_timespan_data(depot.timespan)["b"].last() if
                        category_movie.get_timespan_data(depot.timespan)["b"].last() is not None
                        else 0)
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
