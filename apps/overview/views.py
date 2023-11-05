import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View, generic

from apps.core.mixins import TabContextMixin

# views
from apps.core.utils import (
    change_time_of_date_index_in_df,
    get_merged_value_df_from_queryset,
    sum_up_columns_in_a_dataframe,
)
from apps.users.models import StandardUser


class IndexView(LoginRequiredMixin, TabContextMixin, generic.TemplateView):
    template_name = "overview/index.j2"

    def get_user(self) -> StandardUser:
        return self.request.user  # type: ignore

    def get_stats(self):
        total = 0
        for depot in self.get_user().get_all_active_depots():
            total += float(depot.get_value())
        return {"Total": round(total, 2)}

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
        # return
        return context


class DataApiView(View):
    def get(self, *args, **kwargs):
        active_depots = self.request.user.get_all_active_depots()
        # get the df with all values
        df = get_merged_value_df_from_queryset(active_depots)
        # make the date normal
        df = change_time_of_date_index_in_df(df, 12)
        # sums up all the values
        df = df.fillna(method="ffill").fillna(0)
        df = sum_up_columns_in_a_dataframe(df, drop=False)
        # remove all the rows where the value is 0 as it
        # doesn't make sense in the calculations
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
        return JsonResponse(json_df)
