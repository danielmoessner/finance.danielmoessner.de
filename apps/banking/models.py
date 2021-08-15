from apps.users.models import StandardUser
from apps.core.models import Account as CoreAccount
from apps.core.models import Depot as CoreDepot
from apps.core.utils import turn_dict_of_dicts_into_list_of_dicts, change_time_of_date_index_in_df
from django.db import connection, models
from apps.core import utils
import apps.banking.duplicated_code as banking_duplicated_code
import pandas as pd


class Depot(CoreDepot):
    user = models.ForeignKey(StandardUser, editable=False, related_name="banking_depots",
                             on_delete=models.CASCADE)
    # query optimzation
    balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save(force_insert=force_insert, force_update=force_update, using=using,
                     update_fields=update_fields)
        if self.is_active:
            self.user.banking_depots.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)

    # getters
    def get_date_name_value_chart_data(self, statement):
        cursor = connection.cursor()
        assert str(self.pk) in statement
        cursor.execute(statement)
        data = {}
        for (date, name, value) in cursor.fetchall():
            if date not in data:
                data[date] = {}
            data[date][name] = value
        data = turn_dict_of_dicts_into_list_of_dicts(data, 'date')
        return data

    def get_income_and_expenditure_data(self):
        statement = ("select "
                     "strftime('%Y-%m', banking_change.date) as date, "
                     "banking_category.name ,"
                     "round(sum(banking_change.change)) as change "
                     "from banking_change "
                     "join banking_category on banking_category.id = banking_change.category_id "
                     "where banking_category.depot_id = {} "
                     "group by banking_category.name, strftime('%Y-%m', banking_change.date) "
                     "order by date"
                     ).format(self.pk)
        data = self.get_date_name_value_chart_data(statement)
        return data

    def get_balance_data(self):
        statement = ("select "
                     "strftime('%Y-%W', banking_change.date) as date, "
                     "banking_account.name as name, "
                     "round(avg(banking_change.balance)) as balance "
                     "from banking_change "
                     "join banking_account on banking_account.id = banking_change.account_id "
                     "where depot_id={} "
                     "group by strftime('%Y-%W', banking_change.date), banking_account.name "
                     "order by date"
                     ).format(self.pk)
        data = self.get_date_name_value_chart_data(statement)
        return data

    def get_balance(self):
        if self.balance is None:
            changes = Change.objects.filter(account__in=self.accounts.all(), category__in=self.categories.all())
            banking_duplicated_code.set_balance(self, changes)
        return round(self.balance, 2)

    def get_value(self):
        return self.get_balance()

    def get_value_df(self):
        if not hasattr(self, 'value_df'):
            self.value_df = utils.sum_up_value_dfs_from_items(self.accounts.all())
        return self.value_df

    @staticmethod
    def get_objects_by_user(user):
        return Depot.objects.filter(user=user)

    def get_stats(self):
        balance = self.get_balance()
        if balance is None:
            return {
                'Balance': 'Not calculated'
            }
        return {
            'Balance': balance
        }

    # setters
    def set_balances_to_none(self):
        Depot.objects.filter(pk=self.pk).update(balance=None)
        accounts = Account.objects.filter(depot=self)
        accounts.update(balance=None)
        Category.objects.filter(depot=self).update(balance=None)
        Change.objects.filter(account__in=accounts).update(balance=None)


class Account(CoreAccount):
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name="accounts")
    # query optimzation
    balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    def delete(self, using=None, keep_parents=False):
        self.depot.set_balances_to_none()
        return super().delete(using=using, keep_parents=keep_parents)

    # getters
    def get_balance(self):
        if self.balance is None:
            changes = Change.objects.filter(account=self)
            banking_duplicated_code.set_balance(self, changes)
        return round(self.balance, 2)

    def get_stats(self):
        balance = self.get_balance()
        if balance is None:
            return {'Balance': 'Not calculated'}
        return {
            'Balance': balance
        }

    def get_df_from_database(self, statement, columns):
        assert str(self.pk) in statement
        return utils.get_df_from_database(statement, columns)

    def get_value_df(self):
        if not hasattr(self, 'value_df'):
            # this statement gets the cumulutaive sum of the changes
            statement = """
                select
                    date,
                    sum(change) over (order by date rows between unbounded preceding and current row) as amount
                from (
                    select
                        date(date) as date,
                        sum(change) as change
                    from banking_change
                    where account_id={}
                    group by date(date)
                    order by date
                );
            """.format(self.pk)
            # get and return the df
            df = self.get_df_from_database(statement, ['date', 'value'])
            self.value_df = df
        return self.value_df

    @staticmethod
    def get_objects_by_user(user):
        return Account.objects.filter(depot__in=Depot.objects.filter(user=user))

    @staticmethod
    def get_objects_by_depot(depot):
        return Account.objects.filter(depot=depot)


class Category(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    depot = models.ForeignKey(Depot, editable=False, related_name="categories",
                              on_delete=models.CASCADE)
    # query optimzation
    balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False):
        self.depot.set_balances_to_none()
        return super().delete(using=using, keep_parents=keep_parents)

    # getters
    def get_balance(self):
        if self.balance is None:
            changes = Change.objects.filter(category=self)
            banking_duplicated_code.set_balance(self, changes)
        return round(self.balance, 2)

    def get_stats(self):
        balance = self.get_balance()
        if balance is None:
            return {'Change': 'Not calculated'}
        return {
            'Change': balance
        }

    @staticmethod
    def get_objects_by_user(user):
        return Category.objects.filter(depot__in=Depot.objects.filter(user=user))

    @staticmethod
    def get_objects_by_depot(depot):
        return Category.objects.filter(depot=depot)


class Change(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="changes")
    date = models.DateTimeField()
    category = models.ForeignKey(Category, related_name="changes", null=True, on_delete=models.SET_NULL)
    description = models.TextField(blank=True)
    change = models.DecimalField(decimal_places=2, max_digits=15)
    # query optimization
    balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super(Change, self).__init__(*args, **kwargs)

    def __str__(self):
        return '{} - {}'.format(self.get_date(self.account.depot.user), self.change)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        something_changed = False

        if self.pk is not None:
            change = Change.objects.get(pk=self.pk)

            if (
                    change.account != self.account or change.category != self.category or
                    change.date != self.date or change.change != self.change
            ):
                something_changed = True
                change.set_balances_of_affected_objects_to_null()

        elif self.pk is None:
            something_changed = True

        super().save(force_insert, force_update, using, update_fields)

        if something_changed:
            self.set_balances_of_affected_objects_to_null()

    def delete(self, using=None, keep_parents=False):
        self.set_balances_of_affected_objects_to_null()
        return super().delete(using=using, keep_parents=keep_parents)

    # getters
    @staticmethod
    def get_objects_by_user(user):
        return Change.objects.filter(account__in=Account.get_objects_by_user(user))

    def get_date(self, user):
        # user in args because of sql query optimization
        return self.date.strftime(user.date_format)

    def get_balance(self):
        if self.balance is None:
            changes = Change.objects.filter(account=self.account, date__lte=self.date)
            banking_duplicated_code.set_balance(self, changes)
        return round(self.balance, 2)

    def get_stats(self):
        balance = self.get_balance()
        if balance is None:
            return {
                'Balance': 'Not calculated'
            }
        return {
            'Balance': balance
        }

    def get_description(self):
        description = self.description
        if len(str(self.description)) > 35:
            description = self.description[:35] + "..."
        return description

    # setters
    def set_balances_of_affected_objects_to_null(self):
        Category.objects.filter(pk=self.category.pk).update(balance=None)
        Account.objects.filter(pk=self.account.pk).update(balance=None)
        Change.objects.filter(account=self.account, date__gte=self.date).update(balance=None)
        Depot.objects.filter(pk=self.account.depot.pk).update(balance=None)
