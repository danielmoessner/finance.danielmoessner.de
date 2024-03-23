import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.http import JsonResponse
from django.views import View, generic

from apps.core.mixins import TabContextMixin
from apps.core.utils import (
    change_time_of_date_index_in_df,
    get_merged_value_df_from_queryset,
    sum_up_columns_in_a_dataframe,
)
from apps.overview.builder import build_context_from_buckets
from apps.overview.models import Bucket
from apps.users.mixins import GetUserMixin


def get_value(depot: models.Model) -> float:
    v1 = getattr(depot, "value", 0) or getattr(depot, "balance", 0) or 0
    v2 = round(float(v1), 2)
    return v2


def format_number(number: float) -> str:
    return "{:,.2f}".format(number)


def format_percentage(number: float) -> str:
    return "{:,.2f}%".format(number)


def get_value_stats(depots: list[models.Model]) -> tuple[dict[str, str], float]:
    stats = {}
    total = 0
    for depot in depots:
        if _value := get_value(depot):
            total += _value
            stats[getattr(depot, "name", "---")] = format_number(_value)
    return stats, total


def get_percentage_stats(depots: list[models.Model], total: float) -> dict[str, str]:
    stats = {}
    for depot in depots:
        if _value := get_value(depot):
            percentage = round(_value / total * 100, 2) if total else 0
            stats[f"{getattr(depot, 'name', '')}_percentage"] = format_percentage(
                percentage
            )
    return stats


def get_stats(depots) -> tuple[dict[str, str], str]:
    total = 0
    stats, total = get_value_stats(depots)
    stats.update(get_percentage_stats(depots, total))
    stats["Total"] = format_number(round(total, 2))
    return stats, format_number(total)


class IndexView(
    GetUserMixin, LoginRequiredMixin, TabContextMixin, generic.TemplateView
):
    template_name = "overview/index.j2"

    def get_queryset(self):
        return self.get_user().banking_depots.all()

    def get_buckets(self):
        return Bucket.objects.filter(user=self.get_user())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.get_user()
        user = self.get_user()
        depots = user.get_all_active_depots()
        context["stats"], total = get_stats(depots)
        if context["tab"] == "values":
            context["value_df"] = self.get_value_df()
        if context["tab"] == "charts":
            context["active_depots"] = self.get_user().get_all_active_depots()
        if context["tab"] == "buckets":
            context.update(**build_context_from_buckets(self.get_buckets()))
        return context

    def get_value_df(self):
        active_depots = self.get_user().get_all_active_depots()
        # get the df with all values
        df = get_merged_value_df_from_queryset(active_depots)
        # make the date normal
        df = change_time_of_date_index_in_df(df, 12)
        # sums up all the values
        df = df.ffill().fillna(0)
        df = sum_up_columns_in_a_dataframe(df, drop=False)
        # remove all the rows where the value is 0 as it
        # doesn't make sense in the calculations
        assert df is not None
        df = df.loc[df.loc[:, "value"] != 0]
        # remove duplicate dates and keep the last
        df = df.loc[~df.index.duplicated(keep="last")]
        # rename the columns
        column_names = dict(
            zip(df.columns, ["Total", *[depot.name for depot in active_depots]])
        )
        df = df.rename(columns=column_names)
        # reorder the df
        new_column_order = list(df.columns[1:]) + list([df.columns[0]])
        df = df.loc[:, new_column_order]
        # set the df
        return df


class BucketView(GetUserMixin, LoginRequiredMixin, generic.TemplateView):
    template_name = "overview/bucket.j2"
    context_object_name = "buckets"

    def get_buckets(self):
        path = self.kwargs.get("path")
        buckets = Bucket.objects.filter(user=self.get_user()).filter(
            name__startswith=path
        )
        return buckets

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        path: str = self.kwargs.get("path")
        layers = path.count("/") + 2
        context.update(**build_context_from_buckets(self.get_buckets(), layers))
        return context


class DataApiView(GetUserMixin, View):
    def get(self, *args, **kwargs):
        active_depots = self.get_user().get_all_active_depots()
        # get the df with all values
        df = get_merged_value_df_from_queryset(active_depots)
        # make the date normal
        df = change_time_of_date_index_in_df(df, 12)
        # sums up all the values
        df = df.ffill().fillna(0)
        df = sum_up_columns_in_a_dataframe(df, drop=False)
        # remove all the rows where the value is 0 as it
        # doesn't make sense in the calculations
        assert df is not None
        df = df.loc[df.loc[:, "value"] != 0]
        # remove duplicate dates and keep the last
        df = df.loc[~df.index.duplicated(keep="last")]
        # rename the columns
        column_names = dict(
            zip(df.columns, ["Total", *[depot.name for depot in active_depots]])
        )
        df = df.rename(columns=column_names)
        # reorder the df
        new_column_order = list(df.columns[1:]) + list([df.columns[0]])
        df = df.loc[:, new_column_order]
        # reset the index for json
        df.reset_index(inplace=True)
        # make a json object
        json_df = json.loads(df.to_json(orient="records"))
        # return the df
        return JsonResponse(json_df, safe=False)
