from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Literal, TypedDict, Union

from django.db import connection, models
from django.utils import timezone

import apps.banking.duplicated_code as banking_duplicated_code
from apps.banking.utils import format_currency_amount_to_de
from apps.core import utils
from apps.core.functional import list_create, list_map, list_sort
from apps.core.models import Account as CoreAccount
from apps.core.models import Depot as CoreDepot
from apps.core.utils import turn_dict_of_dicts_into_list_of_dicts
from apps.overview.models import Bucket
from apps.users.models import StandardUser

if TYPE_CHECKING:
    from django.db.models.query import QuerySet


class Depot(CoreDepot):
    user = models.ForeignKey(
        StandardUser,
        editable=False,
        related_name="banking_depots",
        on_delete=models.CASCADE,
    )
    # query optimzation
    balance = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    most_money_moved_away = models.ForeignKey(
        "Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="most_money_moved_away",
    )
    most_money_moved_to = models.ForeignKey(
        "Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="most_money_moved_to",
    )

    if TYPE_CHECKING:
        accounts: QuerySet["Account"]
        categories: QuerySet["Category"]

    # getters
    def get_date_name_value_chart_data(self, statement):
        cursor = connection.cursor()
        assert str(self.pk) in statement
        cursor.execute(statement)
        data = {}
        for dt, name, value in cursor.fetchall():
            if dt not in data:
                data[dt] = {}
            data[dt][name] = value
        data = turn_dict_of_dicts_into_list_of_dicts(data, "date")
        return data

    def get_accounts(self):
        return self.accounts.all()

    def get_total_value(self) -> float:
        return float(self.balance or 0)

    def get_income_and_expenditure_data(self):
        statement = (
            "select "
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
        statement = (
            "select "
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
            self.set_balance()
        assert self.balance is not None
        return round(self.balance, 2)

    def get_value(self):
        return self.get_balance()

    def get_value_df(self):
        if not hasattr(self, "value_df"):
            self.value_df = utils.sum_up_value_dfs_from_items(self.accounts.all())
        return self.value_df

    def get_stats(self):
        balance = self.get_balance()
        if balance is None:
            return {"Balance": "Not calculated"}
        return {"Balance": balance}

    def _get_most_money_moved(
        self, direction: Literal["away", "to"]
    ) -> Union["Account", None]:
        if direction == "away":
            filters = {"change__lt": 0}
        else:
            filters = {"change__gt": 0}
        month_ago = timezone.now() - timezone.timedelta(days=30)
        accounts = list(self.accounts.all())
        max_account: tuple[Account, int] | None = None
        for account in accounts:
            changes_count = Change.objects.filter(
                account=account,
                category__name="Money Movement",
                date__gt=month_ago,
                **filters,
            ).count()
            if not max_account or changes_count > max_account[1]:
                max_account = (account, changes_count)
        return max_account[0] if max_account else None

    # setters
    def set_balances_to_none(self):
        Depot.objects.filter(pk=self.pk).update(balance=None)
        accounts = Account.objects.filter(depot=self)
        accounts.update(balance=None)
        Category.objects.filter(depot=self).update(balance=None)
        Change.objects.filter(account__in=accounts).update(balance=None)

    def calculate_changes_count(self):
        self.most_money_moved_away = self._get_most_money_moved("away")
        self.most_money_moved_to = self._get_most_money_moved("to")

    def reset_balance(self):
        self.balance = None
        self.set_balance()

    def set_balance(self):
        changes = Change.objects.filter(
            account__in=self.accounts.all(), category__in=self.categories.all()
        )
        banking_duplicated_code.set_balance(self, changes)


class Account(CoreAccount):
    TYPE = "Banking"
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name="accounts")
    is_archived = models.BooleanField(default=False)
    DEFAULT_DATE_CHOICES = (
        ("today", "Today"),
        ("last_transaction", "Last Transaction"),
    )
    default_date = models.CharField(
        max_length=20,
        choices=DEFAULT_DATE_CHOICES,
        default="today",
    )
    # query optimzation
    balance = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    # overview
    bucket = models.ForeignKey(
        Bucket,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="banking_items",
    )
    changes_count = models.IntegerField(default=0)

    if TYPE_CHECKING:
        changes: QuerySet["Change"]

    class Meta:
        ordering = ["-changes_count"]

    def __str__(self):
        return f"{self.name}"

    def calculate_changes_count(self):
        month_ago = timezone.now() - timezone.timedelta(days=30)
        self.changes_count = Change.objects.filter(
            account=self, date__gte=month_ago
        ).count()
        self.save()

    def delete(self, using=None, keep_parents=False):
        self.depot.set_balances_to_none()
        return super().delete(using=using, keep_parents=keep_parents)

    def get_bucket_value(self) -> float:
        return float(self.balance or 0)

    def get_balance(self):
        if self.balance is None:
            self.calculate_balance()
        assert self.balance is not None
        return round(self.balance, 2)

    def calculate_balance(self):
        changes = Change.objects.filter(account=self)
        banking_duplicated_code.set_balance(self, changes)

    def transfer_value(self, val: float, date: datetime, description: str):
        category, _ = Category.objects.get_or_create(name="Money Movement")
        Change.objects.create(
            account=self,
            date=date,
            change=val,
            description=description,
            category=category,
        )

    def get_balance_str(self):
        if self.balance is None:
            self.calculate_balance()
        return f"{format_currency_amount_to_de(self.get_balance())} €"

    def get_stats(self):
        return {"Balance": self.get_balance_str()}

    def get_df_from_database(self, statement, columns):
        assert str(self.pk) in statement
        return utils.get_df_from_database(statement, columns)

    def get_value_df(self):
        if not hasattr(self, "value_df"):
            # this statement gets the cumulutaive sum of the changes
            statement = """
                select
                    date,
                    sum(change) over (order by date rows between 
                    unbounded preceding and current row) as amount
                from (
                    select
                        date(date) as date,
                        sum(change) as change
                    from banking_change
                    where account_id={}
                    group by date(date)
                    order by date
                );
            """.format(
                self.pk
            )
            # get and return the df
            df = self.get_df_from_database(statement, ["date", "value"])
            self.value_df = df
        return self.value_df


class YearBalance(TypedDict):
    year: int
    balance: float


class Category(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    depot = models.ForeignKey(
        Depot, editable=False, related_name="categories", on_delete=models.CASCADE
    )
    monthly_budget = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    # query optimzation
    balance = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    changes_count = models.IntegerField(default=0)

    if TYPE_CHECKING:
        changes: QuerySet["Change"]

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
        assert self.balance is not None
        return round(self.balance, 2)

    def get_stats(self):
        stats: dict[str, str | float | int | Decimal] = {"Total": "Not calculated"}
        balance = self.get_balance()
        if balance is not None:
            stats["Total"] = balance
        for sums in self.get_yearly_sum():
            stats[sums["year"]] = sums["balance"]
        return stats

    def get_latest_years_sum(self) -> list[float]:
        sums = {x["year"]: x["balance"] for x in self._get_yearly_sum()}
        now_year = timezone.now().year
        years = list_create(3, now_year, lambda x: x - 1)
        latest_sums = list_map(years, lambda y: sums.get(y, -999999))
        return latest_sums

    def _get_yearly_sum(self) -> list[YearBalance]:
        if not hasattr(self, "_sums"):
            sumsqs = (
                Change.objects.filter(category=self)
                .annotate(year=models.functions.ExtractYear("date"))
                .values("year")
                .annotate(balance=models.Sum("change"))
                .order_by("year")
            )
            sums = list_map(
                sumsqs,
                lambda x: YearBalance(year=x["year"], balance=x["balance"]),
            )
            sums = list_sort(sums, key=lambda x: -int(x["year"]))
            self._sums: list[YearBalance] = sums
        return self._sums

    def get_yearly_sum(self):
        return list_map(
            self._get_yearly_sum(),
            lambda x: {
                "year": str(x["year"]),
                "balance": "{:.2f} €".format(x["balance"]),
            },
        )

    def get_month(self, month: date) -> str:
        if self.monthly_budget is None:
            return "-"
        amount = self.changes.filter(
            date__year=month.year, date__month=month.month
        ).aggregate(total=models.Sum("change"))["total"]
        _amount = abs(amount) if amount is not None else 0
        # check and exclamation mark
        # https://www.alt-codes.net/arrow_alt_codes.php
        if _amount <= self.monthly_budget:
            return "✓ {:.0f} €".format(_amount)
        return "! {:.0f} €".format(_amount - self.monthly_budget)

    def calculate_changes_count(self):
        ago = timezone.now() - timezone.timedelta(days=90)
        self.changes_count = Change.objects.filter(category=self, date__gte=ago).count()
        self.save()

    @staticmethod
    def get_objects_by_depot(depot):
        return Category.objects.filter(depot=depot)


class Change(models.Model):
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="changes"
    )
    date = models.DateTimeField()
    category = models.ForeignKey(
        Category, related_name="changes", on_delete=models.PROTECT
    )
    description = models.TextField(blank=True)
    change = models.DecimalField(decimal_places=2, max_digits=15)
    # query optimization
    balance = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )

    def __init__(self, *args, **kwargs):
        super(Change, self).__init__(*args, **kwargs)

    def __str__(self):
        return "{} - {}".format(self.get_date(self.account.depot.user), self.change)

    def save(self, *args, **kwargs):
        something_changed = False

        if self.pk is not None:
            change = Change.objects.get(pk=self.pk)

            if (
                change.account != self.account
                or change.category != self.category
                or change.date != self.date
                or change.change != self.change
            ):
                something_changed = True
                change.set_balances_of_affected_objects_to_null()

        elif self.pk is None:
            something_changed = True

        super().save(*args, **kwargs)

        if something_changed:
            self.set_balances_of_affected_objects_to_null()

    def delete(self, using=None, keep_parents=False):
        self.set_balances_of_affected_objects_to_null()
        return super().delete(using=using, keep_parents=keep_parents)

    # getters
    def get_date(self, user):
        # user in args because of sql query optimization
        return self.date.strftime(user.date_format)

    def get_balance(self):
        if self.balance is None:
            changes = Change.objects.filter(account=self.account, date__lte=self.date)
            banking_duplicated_code.set_balance(self, changes)
        assert self.balance is not None
        return round(self.balance, 2)

    def get_stats(self):
        balance = self.get_balance()
        if balance is None:
            return {"Balance": "Not calculated"}
        return {"Balance": balance}

    def get_description(self):
        description = self.description
        if len(str(self.description)) > 35:
            description = self.description[:35] + "..."
        return description

    # setters
    def set_balances_of_affected_objects_to_null(self):
        Category.objects.filter(pk=self.category.pk).update(balance=None)
        Account.objects.filter(pk=self.account.pk).update(balance=None)
        Change.objects.filter(account=self.account, date__gte=self.date).update(
            balance=None
        )
        Depot.objects.get(pk=self.account.depot.pk).reset_balance()
