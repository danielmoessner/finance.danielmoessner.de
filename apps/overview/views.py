import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View, generic

from apps.core.mixins import AjaxResponseMixin, CustomAjaxDeleteMixin, GetFormWithDepotAndInitialDataMixin, GetFormWithUserMixin, TabContextMixin
from apps.core.utils import (
    change_time_of_date_index_in_df,
    get_merged_value_df_from_queryset,
    sum_up_columns_in_a_dataframe,
)
from apps.overview.forms import BucketForm
from apps.overview.models import Bucket
from apps.users.mixins import GetUserMixin


class IndexView(
    GetUserMixin, LoginRequiredMixin, TabContextMixin, generic.TemplateView
):
    template_name = "overview/index.j2"

    def get_stats(self):
        total = 0
        stats = {}
        depots = self.get_user().get_all_active_depots()

        def get_value(depot) -> float:
            v1 = getattr(depot, "value", 0) or getattr(depot, "balance", 0) or 0
            v2 = round(float(v1), 2)
            return v2
        
        def format_number(number: float) -> str:
            return "{:,.2f}".format(number)
        
        def format_percentage(number: float) -> str:
            return "{:,.2f}%".format(number)

        for depot in depots:
            if _value := get_value(depot):
                total += _value
                stats[depot.name] = format_number(_value)
        
        for depot in depots:
            if _value := get_value(depot):
                percentage = round(_value / total * 100, 2)
                stats[f"{depot.name}_percentage"] = format_percentage(percentage)

        stats["Total"] = format_number(round(total, 2))


        return stats

    def get_value_df(self):
        active_depots = self.get_user().get_all_active_depots()
        # get the df with all values
        df = get_merged_value_df_from_queryset(active_depots)
        # make the date normal
        df = change_time_of_date_index_in_df(df, 12)
        # sums up all the values
        df = df.fillna(method="ffill").fillna(0)
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

    def get_queryset(self):
        return self.get_user().banking_depots.all()

    def get_context_data(self, **kwargs):
        # general
        context = super(IndexView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        # specific
        context["stats"] = self.get_stats()
        if context["tab"] == "values":
            context["value_df"] = self.get_value_df()
        if context["tab"] == "charts":
            context["active_depots"] = self.get_user().get_all_active_depots()
        if context["tab"] == "buckets":
            context["buckets"] = Bucket.objects.filter(user=self.get_user())
        # return
        return context


class DataApiView(GetUserMixin, View):
    def get(self, *args, **kwargs):
        active_depots = self.get_user().get_all_active_depots()
        # get the df with all values
        df = get_merged_value_df_from_queryset(active_depots)
        # make the date normal
        df = change_time_of_date_index_in_df(df, 12)
        # sums up all the values
        df = df.fillna(method="ffill").fillna(0)
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


class AddBucketView(
    GetUserMixin,
    GetFormWithUserMixin,
    AjaxResponseMixin,
    generic.CreateView,
):
    model = Bucket
    form_class = BucketForm
    template_name = "symbols/form_snippet.j2"


class EditBucketView(
    GetUserMixin,
    GetFormWithUserMixin,
    AjaxResponseMixin,
    generic.UpdateView,
):
    model = Bucket
    form_class = BucketForm
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return Bucket.objects.filter(user=self.get_user())


class DeleteBucketView(GetUserMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Bucket
    template_name = "symbols/delete_snippet.j2"

    def get_queryset(self):
        return Bucket.objects.filter(user=self.get_user())
