import pandas as pd
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.mixins import TabContextMixin
from django.views import generic


# views
from apps.core.utils import get_merged_value_df_from_queryset, sum_up_columns_in_a_dataframe, \
    change_time_of_date_index_in_df


class IndexView(LoginRequiredMixin, TabContextMixin, generic.TemplateView):
    template_name = "overview/index.j2"

    def get_stats(self):
        total = 0
        for depot in self.request.user.get_all_active_depots():
            total += float(depot.get_value())
        return {
            'Total': round(total, 2)
        }

    def get_value_df(self):
        pd.set_option('max_columns', None)
        # get the df with all values
        df = get_merged_value_df_from_queryset(self.request.user.get_all_active_depots())
        # make the date normal
        df = change_time_of_date_index_in_df(df, 12)
        # sums up all the values
        df = df.fillna(method="ffill").fillna(0)
        df = sum_up_columns_in_a_dataframe(df, drop=False)
        # remove all the rows where the value is 0 as it doesn't make sense in the calculations
        df = df.loc[df.loc[:, 'value'] != 0]
        # remove duplicate dates and keep the last
        df = df.loc[~df.index.duplicated(keep='last')]
        # set the df
        return df

    def get_queryset(self):
        return self.request.user.banking_depots.all()

    def get_context_data(self, **kwargs):
        # general
        context = super(IndexView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        # specific
        context['stats'] = self.get_stats()
        if context['tab'] == 'values':
            context['value_df'] = self.get_value_df()
        # return
        return context
