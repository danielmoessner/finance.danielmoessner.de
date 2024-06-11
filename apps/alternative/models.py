from typing import TYPE_CHECKING, Union

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

import apps.core.return_calculation as rc
import apps.core.utils as utils
from apps.core.models import Depot as CoreDepot
from apps.overview.models import Bucket
from apps.users.models import StandardUser


class Depot(CoreDepot):
    user = models.ForeignKey(
        StandardUser,
        editable=False,
        related_name="alternative_depots",
        on_delete=models.CASCADE,
    )
    # query optimization
    value = models.FloatField(null=True)

    if TYPE_CHECKING:
        alternatives: QuerySet["Alternative"]

    # getters
    def get_accounts(self):
        return []

    def get_total_value(self) -> float:
        return float(self.value or 0)

    def get_stats(self):
        return {"Value": self.get_value_display()}

    def get_value_display(self) -> str:
        if self.value is None:
            return "404"
        return "{:,.2f} €".format(self.value)

    def __get_number_from_database(self, statement):
        assert str(self.pk) in statement
        return utils.get_number_from_database(statement)

    def get_value_df(self):
        if not hasattr(self, "value_df"):
            self.value_df = utils.sum_up_value_dfs_from_items(self.alternatives.all())
        return self.value_df

    # setters
    def reset(self):
        self.value = None
        self.recalculate()

    def recalculate(self):
        self.calculate_value()
        self.save()

    def calculate_value(self):
        statement = """
            select sum(value) as value
            from alternative_value v
            left join alternative_alternative a on v.alternative_id = a.id
            where depot_id = {}
            and (date, alternative_id) in (
                select max(date) as date, v.alternative_id
                from alternative_value v
                group by v.alternative_id
            )
            """.format(
            self.pk
        )
        self.value = self.__get_number_from_database(statement)

    def reset_all(self):
        for alternative in self.alternatives.all():
            alternative.reset()
        self.reset()


class Alternative(models.Model):
    name = models.CharField(max_length=200)
    depot = models.ForeignKey(
        Depot, on_delete=models.CASCADE, related_name="alternatives"
    )
    # query optimization
    invested_capital = models.FloatField(null=True)
    current_return = models.FloatField(null=True)
    profit = models.FloatField(null=True)
    # overview
    bucket = models.ForeignKey(
        Bucket,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alternative_items",
    )

    if TYPE_CHECKING:
        values: QuerySet["Value"]
        flows: QuerySet["Flow"]

    class Meta:
        unique_together = ("depot", "name")

    def __str__(self):
        return "{}".format(self.name)

    # getters
    def get_bucket_value(self) -> float:
        value = self.get_value()
        return float(value or 0)

    def get_stats(self):
        return {
            "Value": self.get_value_display(),
            "Invested Capital": self.get_invested_capital_display(),
            "Current Return": self.get_current_return_display(),
            "Profit": self.get_profit_display(),
        }

    def __get_value(self) -> Union["Value", None]:
        value = Value.objects.filter(alternative=self).order_by("date").last()
        return value

    def get_value(self):
        value = self.__get_value()
        if value:
            return value.value
        return None

    def get_value_display(self) -> str:
        value = self.get_value()
        if value is not None:
            return "{:.2f} €".format(value)
        return "404"

    def get_profit_display(self) -> str:
        if self.profit is not None:
            return "{:.2f} €".format(self.profit)
        return "404"

    def get_invested_capital_display(self) -> str:
        if self.invested_capital is not None:
            return "{:.2f} €".format(self.invested_capital)
        return "404"

    def get_current_return_display(self):
        if self.current_return is not None:
            return "{:.0f} %".format(self.current_return * 100)
        return "404"

    def get_value_df(self):
        if not hasattr(self, "value_df"):
            statement = """
                select date(date) as date,
                       value      as value
                from alternative_value v
                where v.alternative_id = {}
                  and v.date in (
                    select max(date)
                    from alternative_value
                    where alternative_id = {}
                    group by date(date)
                )
            """.format(
                self.pk, self.pk
            )
            # get the flow df
            self.value_df = utils.get_df_from_database(statement, ["date", "value"])
        return self.value_df

    def get_flow_df(self):
        if not hasattr(self, "flow_df"):
            statement = """
                select 
                    date(date) as date,
                    sum(flow) as flow
                from alternative_flow f
                join alternative_alternative a on f.alternative_id=a.id
                where a.id = {}
                group by date(date)
            """.format(
                self.pk
            )
            # get the flow df
            self.flow_df = utils.get_df_from_database(statement, ["date", "flow"])
        return self.flow_df

    def get_flows_and_values(self):
        flows = list(self.flows.all().values("date", "flow", "pk"))
        values = list(self.values.all().values("date", "value", "pk"))
        flows_and_values = flows + values
        flows_and_values_sorted = sorted(flows_and_values, key=lambda k: k["date"])
        return flows_and_values_sorted

    # setters
    def reset(self):
        self.current_return = None
        self.invested_capital = None
        self.profit = None
        self.recalculate()
        self.save()

    def recalculate(self):
        current_return_df = rc.get_current_return_df(
            self.get_flow_df(), self.get_value_df()
        )
        self.calculate_current_return(current_return_df)
        self.calculate_invested_capital(current_return_df)
        self.calculate_profit()
        self.save()

    def calculate_current_return(self, current_return_df):
        self.current_return = rc.get_current_return(current_return_df)

    def calculate_invested_capital(self, current_return_df):
        self.invested_capital = rc.get_invested_capital(current_return_df)

    def calculate_profit(self):
        self.profit = None
        value = self.__get_value()
        if self.invested_capital is not None and value is not None:
            self.profit = float(value.value) - float(self.invested_capital)


class Value(models.Model):
    alternative = models.ForeignKey(
        Alternative, related_name="values", on_delete=models.CASCADE
    )
    date = models.DateTimeField()
    value = models.DecimalField(
        decimal_places=2, max_digits=15, validators=[MinValueValidator(0)]
    )

    class Meta:
        unique_together = ("alternative", "date")

    def __str__(self):
        return "{}: {} {}".format(self.alternative, self.get_date(), self.value)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.reset_deps()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.reset_deps()

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%y %H:%M")

    # setters
    def reset_deps(self):
        self.alternative.reset()
        self.alternative.depot.reset()


class Flow(models.Model):
    alternative = models.ForeignKey(
        Alternative, related_name="flows", on_delete=models.CASCADE
    )
    date = models.DateTimeField()
    flow = models.DecimalField(decimal_places=2, max_digits=15)

    class Meta:
        unique_together = ("alternative", "date")

    def __str__(self):
        return "{}: {} {}".format(self.alternative, self.get_date(), self.flow)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime("%d.%m.%y %H:%M")

    # setters
    def reset_deps(self):
        self.alternative.reset()
        self.alternative.depot.reset()
