from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db import models
from apps.users.models import StandardUser
from apps.core.models import Depot as CoreDepot
import apps.core.return_calculation as rc
import apps.core.utils as utils


class Depot(CoreDepot):
    user = models.ForeignKey(StandardUser, editable=False, related_name="alternative_depots", on_delete=models.CASCADE)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save(force_insert=force_insert, force_update=force_update, using=using,
                     update_fields=update_fields)
        if self.is_active:
            self.user.alternative_depots.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)

    # getters
    def get_stats(self):
        return {
            'Value': self.get_value()
        }

    def get_value(self):
        if not hasattr(self, 'value'):
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
            """.format(self.pk)
            self.value = self.get_number_from_database(statement)
        return self.value

    def get_number_from_database(self, statement):
        assert str(self.pk) in statement
        return utils.get_number_from_database(statement)


class Alternative(models.Model):
    name = models.CharField(max_length=200)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name="alternatives")
    # query optimization
    invested_capital = models.FloatField(null=True)
    time_weighted_return = models.FloatField(null=True)
    internal_rate_of_return = models.FloatField(null=True)
    current_return = models.FloatField(null=True)
    profit = models.FloatField(null=True)

    class Meta:
        unique_together = ("depot", "name")

    def __str__(self):
        return '{}'.format(self.name)

    # getters
    def get_stats(self):
        return {
            'Value': self.get_value(),
            'Invested Capital': self.get_invested_capital(),
            'Current Return': self.get_current_return(),
            'Time Weighted Return': self.get_time_weighted_return(),
            'Internal Rate of Return': self.get_internal_rate_of_return()
        }

    def get_value(self):
        value = Value.objects.filter(alternative=self).order_by('date').last()
        if value:
            return float(value.value)
        return None

    def get_profit(self):
        if self.profit is None:
            invested_capital = self.get_invested_capital()
            value = self.get_value()
            if invested_capital and value:
                self.profit = value - invested_capital
            else:
                self.profit = None
            self.save()
        return self.profit

    def get_invested_capital(self):
        if self.invested_capital is None:
            df = rc.get_current_return_df(self.get_flow_df(), self.get_value_df())
            self.invested_capital = rc.get_invested_capital(df)
            self.save()
        return self.invested_capital

    def get_time_weighted_return(self):
        if self.time_weighted_return is None:
            time_weighted_return_df = rc.get_time_weighted_return_df(self.get_flow_df(), self.get_value_df())
            self.time_weighted_return = rc.get_time_weighted_return(time_weighted_return_df)
            self.save()
        return self.time_weighted_return

    def get_internal_rate_of_return(self):
        if self.internal_rate_of_return is None:
            internal_rate_of_return_df = rc.get_internal_rate_of_return_df(self.get_flow_df(), self.get_value_df())
            self.internal_rate_of_return = rc.get_internal_rate_of_return(internal_rate_of_return_df)
            self.save()
        return self.internal_rate_of_return

    def get_current_return(self):
        if self.current_return is None:
            current_return_df = rc.get_current_return_df(self.get_flow_df(), self.get_value_df())
            self.current_return = rc.get_current_return(current_return_df)
            self.save()
        return self.current_return

    def get_value_df(self):
        if not hasattr(self, 'value_df'):
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
            """.format(self.pk, self.pk)
            # get the flow df
            self.value_df = self.get_df_from_database(statement, ['date', 'value'])
        return self.value_df

    def get_df_from_database(self, statement, columns):
        assert str(self.pk) in statement
        return utils.get_df_from_database(statement, columns)

    def get_flow_df(self):
        if not hasattr(self, 'flow_df'):
            statement = """
                select 
                    date(date) as date,
                    sum(flow) as flow
                from alternative_flow f
                join alternative_alternative a on f.alternative_id=a.id
                where a.id = {}
                group by date(date)
            """.format(self.pk)
            # get the flow df
            self.flow_df = self.get_df_from_database(statement, ['date', 'flow'])
        return self.flow_df

    def get_flows_and_values(self):
        flows = list(self.flows.all().values('date', 'flow', 'pk'))
        values = list(self.values.all().values('date', 'value', 'pk'))
        flows_and_values = flows + values
        flows_and_values_sorted = sorted(flows_and_values, key=lambda k: k['date'])
        return flows_and_values_sorted

    # setters
    def reset(self):
        self.current_return = None
        self.internal_rate_of_return = None
        self.invested_capital = None
        self.time_weighted_return = None
        self.save()


class Value(models.Model):
    alternative = models.ForeignKey(Alternative, related_name="values", on_delete=models.CASCADE)
    date = models.DateTimeField()
    value = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ("alternative", "date")

    def __str__(self):
        return '{}: {} {}'.format(self.alternative, self.get_date(), self.value)

    def save(self, *args, **kwargs):
        self.alternative.reset()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.alternative.reset()
        super().delete(*args, **kwargs)

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime('%d.%m.%y %H:%M')


class Flow(models.Model):
    alternative = models.ForeignKey(Alternative, related_name="flows", on_delete=models.CASCADE)
    date = models.DateTimeField()
    flow = models.DecimalField(decimal_places=2, max_digits=15)

    class Meta:
        unique_together = ("alternative", "date")

    def __str__(self):
        return '{}: {} {}'.format(self.alternative, self.get_date(), self.flow)

    def save(self, *args, **kwargs):
        self.alternative.reset()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.alternative.reset()
        super().delete(*args, **kwargs)

    # getters
    def get_date(self):
        return timezone.localtime(self.date).strftime('%d.%m.%y %H:%M')
