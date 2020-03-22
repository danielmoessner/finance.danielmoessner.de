from django.db import connection
from django.db import models

from apps.users.models import StandardUser
from apps.core.models import Timespan as CoreTimespan
from apps.core.models import Account as CoreAccount
from apps.core.models import Depot as CoreDepot
from apps.core.utils import turn_dict_of_dicts_into_list_of_dicts
import apps.banking.duplicated_code as banking_duplicated_code
import apps.core.duplicated_code as dc


class Depot(CoreDepot):
    user = models.ForeignKey(StandardUser, editable=False, related_name="banking_depots",
                             on_delete=models.CASCADE)
    # query optimzation
    balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

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
        return self.balance

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

    # getters
    def get_balance(self):
        if self.balance is None:
            changes = Change.objects.filter(account=self)
            banking_duplicated_code.set_balance(self, changes)
        return self.balance

    def get_stats(self):
        balance = self.get_balance()
        if balance is None:
            return {'Balance': 'Not calculated'}
        return {
            'Balance': balance
        }

    def get_latest_picture(self):
        return dc.get_latest_picture(self)

    @staticmethod
    def get_objects_by_user(user):
        return Account.objects.filter(depot__in=Depot.objects.filter(user=user))

    @staticmethod
    def get_objects_by_depot(depot):
        return Account.objects.filter(depot=depot)


class Category(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    depot = models.ForeignKey(Depot, editable=False, related_name="categories",
                              on_delete=models.CASCADE)
    # query optimzation
    balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name

    # getters
    def get_balance(self):
        if self.balance is None:
            changes = Change.objects.filter(category=self)
            banking_duplicated_code.set_balance(self, changes)
        return self.balance

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

    @staticmethod
    def get_default_category():
        return Category.objects.get_or_create(
            name="Default Category",
            description="This category was created because the original category got deleted.")


class Change(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="changes")
    date = models.DateTimeField()
    category = models.ForeignKey(Category, related_name="changes", null=True,
                                 on_delete=models.SET_NULL)
    description = models.TextField(blank=True)
    change = models.DecimalField(decimal_places=2, max_digits=15)
    # query optimization
    balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super(Change, self).__init__(*args, **kwargs)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.pk:
            change = Change.objects.get(pk=self.pk)

            if (
                    change.account != self.account or change.category != self.category or
                    change.date != self.date or change.change != self.change
            ):
                change.set_balances_of_affected_objects_to_null()

        super().save(force_insert, force_update, using, update_fields)
        self.set_balances_of_affected_objects_to_null()

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
        return self.balance

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


class Timespan(CoreTimespan):
    depot = models.ForeignKey(Depot, editable=False, related_name="timespans", on_delete=models.CASCADE)
