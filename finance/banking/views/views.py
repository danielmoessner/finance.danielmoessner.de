from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic

from finance.banking.models import Timespan
from finance.banking.models import Category
from finance.banking.models import Account
from finance.banking.models import Movie
from finance.banking.models import Depot

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import timedelta
import pandas as pd


# VIEWS
class IndexView(generic.TemplateView):
    template_name = "banking_index.njk"

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        context["depot"] = context["user"].banking_depots.get(is_active=True)
        context["accounts"] = context["depot"].accounts.order_by("name")
        context["categories"] = context["depot"].categories.order_by("name")
        context["timespans"] = context["depot"].timespans.all()
        context["timespan"] = context["depot"].timespans.get(is_active=True)
        print(context["timespan"])

        context["movie"] = context["depot"].movies.get(account=None, category=None)
        context["accounts_movies"] = zip(context["accounts"], context["depot"].movies.filter(
            account__in=context["accounts"], category=None).order_by("account__name"))
        return context


class AccountView(generic.TemplateView):
    template_name = "banking_account.njk"

    def get_context_data(self, **kwargs):
        context = super(AccountView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        context["depot"] = context["user"].banking_depots.get(is_active=True)
        context["accounts"] = context["depot"].accounts.order_by("name")
        context["categories"] = context["depot"].categories.order_by("name")
        context["timespans"] = context["depot"].timespans.all()
        context["timespan"] = context["depot"].timespans.get(is_active=True)

        context["account"] = context["depot"].accounts.get(slug=kwargs["slug"])
        context["movie"] = context["depot"].movies.get(account=context["account"], category=None)
        context["changes"] = context["account"].changes.order_by("-date", "-pk").select_related(
            "category")
        # pictures = context["movie"].pictures.filter(change__in=changes).order_by("d", "pk")
        # context["changes_pictures"] = zip(changes, pictures)
        return context


class CategoryView(generic.TemplateView):
    template_name = "banking_category.njk"

    def get_context_data(self, **kwargs):
        context = super(CategoryView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        context["depot"] = context["user"].banking_depots.get(is_active=True)
        context["accounts"] = context["depot"].accounts.order_by("name")
        context["categories"] = context["depot"].categories.order_by("name")
        context["timespans"] = context["depot"].timespans.all()
        context["timespan"] = context["depot"].timespans.get(is_active=True)

        context["category"] = context["depot"].categories.get(slug=kwargs["slug"])
        context["movie"] = context["depot"].movies.get(account=None, category=context["category"])
        context["changes"] = context["category"].changes.order_by("-date", "-pk").select_related(
            "account")
        # pictures = context["movie"].pictures.filter(change__in=changes).order_by("d", "pk")
        # context["changes_pictures"] = zip(changes, pictures)
        return context


# FUNCTIONS
def update_movies(request, user_slug):
    depot = request.user.banking_depots.get(is_active=True)
    Movie.update_all(depot)
    return HttpResponseRedirect(reverse_lazy("banking:index", args=[request.user.slug, ]))


# API
class IndexData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, user_slug):
        user = request.user
        depot = Depot.objects.get(user=user, is_active=True)

        timespan = depot.timespans.get(is_active=True)
        df1 = depot.get_movie().get_df(timespan)
        df1.rename(columns={"d": "dates", "b": "Total"}, inplace=True)
        df1.drop(["c"], axis=1, inplace=True)
        df1.set_index("dates", inplace=True)
        for account in Account.objects.filter(depot=depot):
            df2 = account.get_movie().get_df(timespan)
            if df2.empty:
                continue
            df2.rename(columns={"d": "dates", "b": str(account)}, inplace=True)
            df2.drop(["c"], axis=1, inplace=True)
            df2.set_index("dates", inplace=True)
            df1 = pd.concat([df1, df2], join="outer", ignore_index=False, sort=False)
        df1.sort_index(inplace=True)
        df1.ffill(inplace=True)
        df1 = df1[~df1.index.duplicated(keep="last")]
        df1.fillna(0, inplace=True)

        datasets = list()
        for column_name in df1.columns.values.tolist():
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
        account = Account.objects.get(slug=slug)

        movie = account.get_movie()
        timespan = depot.timespans.get(is_active=True)
        df = movie.get_df(timespan)
        if df.empty:
            return Response(dict())
        df.drop(["c"], axis=1, inplace=True)
        df["d"] = df["d"].dt.date
        df.rename(columns={"d": "dates", "b": "balance"}, inplace=True)
        df.set_index("dates", inplace=True)
        df = df.groupby(df.index).last()

        for category in depot.categories.all():
            df_c = account.get_cat_movie(category).get_df(timespan)
            if df_c.empty:
                continue
            df_c = df_c.drop(["b"], axis=1)
            df_c["d"] = df_c["d"].dt.date
            df_c.rename(columns={"d": "dates", "c": str(category)}, inplace=True)
            df_c.set_index("dates", inplace=True)
            for index in df_c.index.get_duplicates():
                for column in df_c.columns:
                    df_c.loc[index, column] = df_c.loc[index, column].sum()
            df_c = df_c.groupby(df_c.index).last()
            df = pd.concat([df, df_c], axis=1, sort=False)
        df.sort_index(inplace=True)

        # df with all dates to normalize the data oterhwise chartjs displays the date weird af
        dates = pd.date_range(start=df.index[0], end=(df.index[-1] + timedelta(days=1)))
        df_d = pd.DataFrame({"dates": dates})
        df_d["dates"] = df_d["dates"].dt.date
        df_d.set_index("dates", inplace=True)
        df = pd.concat([df, df_d], axis=1, sort=True)
        df["balance"].ffill(inplace=True)
        df.fillna(0, inplace=True)

        datasets = list()
        dataset = dict()
        dataset["label"] = "Balance"
        dataset["type"] = "line"
        dataset["data"] = df["balance"].values
        datasets.append(dataset)
        for column in df.drop(["balance"], axis=1).columns:
            dataset = dict()
            dataset["label"] = str(column)
            dataset["type"] = "bar"
            dataset["data"] = df[column].tolist()
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
        depot = user.banking_depots.get(is_active=True)
        category = Category.objects.get(slug=slug)
        timespan = depot.timespans.get(is_active=True)

        df = category.get_movie().get_df(timespan)
        df.rename(columns={"d": "date", "c": "change"}, inplace=True)
        df.drop(["b"], axis=1, inplace=True)
        df.set_index("date", inplace=True)
        first_date = min(df.index)
        last_date = max(df.index)
        date_range = pd.date_range(first_date, last_date, freq="27D")
        df_date_range = pd.DataFrame(0, index=date_range, columns=["change"])
        df = pd.concat([df, df_date_range], sort=False)
        df = df.groupby(lambda x: (x.year, x.month)).sum()
        df.index.name = "date"
        df.index = df.index.map(lambda val: str(val[1]) + "/" + str(val[0]))

        dataset = dict()
        dataset["data"] = df["change"].tolist()
        dataset["label"] = "Change"
        if len(df["change"]) > 0:
            dataset["backgroundColor"] = "hsla(358, 100%, 50%, 1)" if df["change"].sum() < 0 \
                else "hsla(140, 100%, 50%, 1)"
        datasets = list()
        datasets.append(dataset)
        data = dict()
        data["datasets"] = datasets
        data["labels"] = df.index.tolist()

        return Response(data)


class CategoriesData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, user_slug):
        user = request.user
        depot = user.banking_depots.get(is_active=True)
        categories = depot.categories.all()
        movies = depot.movies.filter(account=None, category__in=categories).select_related(
            "category")

        labels_data = list()
        for movie in movies:
            value = movie.get_values(user, ["b", ], depot.timespans.get(is_active=True))
            if value != 0:
                labels_data.append((str(movie.category), value["b"]))
        labels_data.sort(key=lambda x: x[1])
        labels = [l for l, d in labels_data]
        data = [abs(d) for l, d in labels_data]
        datasets_data = dict()
        datasets_data["data"] = data
        datasets = list()
        datasets.append(datasets_data)

        data = dict()
        data["datasets"] = datasets
        data["labels"] = labels
        return Response(data)
