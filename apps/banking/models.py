import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Literal, TypedDict, Union
from uuid import uuid4

import pandas as pd
import requests
from django.contrib.sessions.backends.base import SessionBase
from django.db import connection, models, transaction
from django.utils import timezone
from pydantic import BaseModel

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

    def _get_statements_df(self):
        changes = (
            Change.objects.filter(
                account__in=self.accounts.all(),
            )
            .filter(date__gte=timezone.now() - timezone.timedelta(days=365))
            .values_list("date", "category__name", "change")
            .order_by("category__changes_count")
        )
        df = pd.DataFrame(changes, columns=["date", "category", "change"])
        df["month"] = pd.to_datetime(df["date"]).dt.to_period("M")
        monthly_summary = (
            df.groupby(["month", "category"])["change"].sum().reset_index()
        )
        monthly_summary = monthly_summary.sort_values("month", ascending=False)
        monthly_summary["month"] = monthly_summary["month"].dt.strftime("%B %y")
        return monthly_summary

    def get_statements(self):
        df = self._get_statements_df()
        months = df["month"].unique().tolist()
        categories = df["category"].unique().tolist()

        result = {"months": months, "data": {}}

        for category in categories:
            result["data"][category] = [0.0] * len(months)

        for _, row in df.iterrows():
            month = row["month"]
            category = row["category"]
            amount = float(row["change"])

            month_index = months.index(month)
            result["data"][category][month_index] = amount

        return result

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
        comdirect_import: Union["ComdirectImport", None]
        csv_import: Union["CsvImport", None]

    class Meta:
        ordering = ["-changes_count"]

    def __str__(self):
        return f"{self.name}"

    def get_import(self) -> Union["ComdirectImport", "CsvImport", None]:
        if hasattr(self, "comdirect_import"):
            return self.comdirect_import
        if hasattr(self, "csv_import"):
            return self.csv_import
        return None

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
    is_archived = models.BooleanField(default=False)
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

    @property
    def monthly_budget_str(self):
        if self.monthly_budget is None:
            return ""
        return f"({round(self.monthly_budget, 0)} €)"

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
        return "❗ {:.0f} €".format(_amount)

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

    if TYPE_CHECKING:
        comdirect_import_changes: QuerySet["ComdirectImportChange"]

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
        with transaction.atomic():
            self.comdirect_import_changes.update(is_deleted=True)
            ret = super().delete(using=using, keep_parents=keep_parents)
        return ret

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


class CsvImport(models.Model):
    account = models.OneToOneField(
        Account, on_delete=models.CASCADE, related_name="csv_import"
    )
    map = models.JSONField()

    def __str__(self):
        return f"{self.account} Import Map"

    class Meta:
        verbose_name = "Import Map"
        verbose_name_plural = "Import Maps"


class ComdirectImport(models.Model):
    account = models.OneToOneField(
        Account, on_delete=models.CASCADE, related_name="comdirect_import"
    )
    comdirect_api_client_id = models.CharField(max_length=255)
    comdirect_api_client_secret = models.CharField(max_length=255)
    comdirect_zugangsnummer = models.CharField(max_length=255)
    comdirect_pin = models.CharField(max_length=255)
    comdirect_account_id = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    OAUTH_URL = "https://api.comdirect.de"
    API_URL = "https://api.comdirect.de/api"

    if TYPE_CHECKING:
        changes: QuerySet["ComdirectImportChange"]

    class Meta:
        verbose_name = "Comdirect Import"
        verbose_name_plural = "Comdirect Imports"

    def __str__(self):
        return f"Comdirect Import for {self.account.name}"

    def _get_tokens(self) -> dict[str, str]:
        resp = requests.post(
            f"{self.OAUTH_URL}/oauth/token",
            data={
                "client_id": self.comdirect_api_client_id,
                "client_secret": self.comdirect_api_client_secret,
                "username": self.comdirect_zugangsnummer,
                "password": self.comdirect_pin,
                "grant_type": "password",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        data = resp.json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        return {"access_token": access_token, "refresh_token": refresh_token}

    def _get_session_identifier(self, access_token: str) -> dict[str, str | int]:
        request_id = int(datetime.now().timestamp())
        session_id = uuid4().hex
        resp = requests.get(
            f"{self.API_URL}/session/clients/user/v1/sessions",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "x-http-request-info": json.dumps(
                    {
                        "clientRequestId": {
                            "sessionId": session_id,
                            "requestId": request_id,
                        }
                    }
                ),
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        identifier = data[0]["identifier"]
        return {
            "identifier": identifier,
            "session_id": session_id,
            "request_id": request_id,
        }

    def _validate_session(
        self, access_token: str, session_id: str, request_id: int, identifier: str
    ) -> dict[str, str]:
        resp = requests.post(
            f"{self.API_URL}/session/clients/user/v1/sessions/{identifier}/validate",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "x-http-request-info": json.dumps(
                    {
                        "clientRequestId": {
                            "sessionId": session_id,
                            "requestId": request_id,
                        }
                    }
                ),
                "Content-Type": "application/json",
            },
            json={
                "identifier": identifier,
                "sessionTanActive": True,
                "activated2FA": True,
            },
        )
        resp.raise_for_status()
        challenge_id = json.loads(resp.headers["x-once-authentication-info"])["id"]
        return {"challenge_id": challenge_id}

    def _activate_session(
        self,
        access_token: str,
        session_id: str,
        request_id: int,
        identifier: str,
        challenge_id: str,
    ) -> None:
        resp = requests.patch(
            f"{self.API_URL}/session/clients/user/v1/sessions/{identifier}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "x-http-request-info": json.dumps(
                    {
                        "clientRequestId": {
                            "sessionId": session_id,
                            "requestId": request_id,
                        }
                    }
                ),
                "Content-Type": "application/json",
                "x-once-authentication-info": json.dumps({"id": challenge_id}),
                "x-once-authentication": "000000",
            },
            json={
                "identifier": identifier,
                "sessionTanActive": True,
                "activated2FA": True,
            },
        )
        resp.raise_for_status()

    def _get_api_tokens(self, access_token: str) -> dict[str, str]:
        resp = requests.post(
            f"{self.OAUTH_URL}/oauth/token",
            data={
                "client_id": self.comdirect_api_client_id,
                "client_secret": self.comdirect_api_client_secret,
                "token": access_token,
                "grant_type": "cd_secondary",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        data = resp.json()
        api_access_token = data["access_token"]
        api_refresh_token = data["refresh_token"]
        return {
            "api_access_token": api_access_token,
            "api_refresh_token": api_refresh_token,
        }

    def _refresh_tokens(self, api_refresh_token: str) -> dict[str, str]:
        resp = requests.post(
            f"{self.OAUTH_URL}/oauth/token",
            data={
                "client_id": self.comdirect_api_client_id,
                "client_secret": self.comdirect_api_client_secret,
                "refresh_token": api_refresh_token,
                "grant_type": "refresh_token",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        data = resp.json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        return {"api_access_token": access_token, "api_refresh_token": refresh_token}

    def get_transactions(
        self, api_access_token: str, session_id: str, request_id: int, page: int
    ) -> None:
        resp = requests.get(
            f"{self.API_URL}/banking/v1/accounts/{self.comdirect_account_id}/transactions",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {api_access_token}",
                "x-http-request-info": json.dumps(
                    {
                        "clientRequestId": {
                            "sessionId": session_id,
                            "requestId": request_id,
                        }
                    }
                ),
                "Content-Type": "application/json",
            },
            params={
                "transactionState": "BOOKED",
                "paging-first": page * 20,
                "paging-count": 20,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data

    def start_login_flow(self, session: SessionBase):
        data = {}
        data.update(self._get_tokens())
        data.update(self._get_session_identifier(data["access_token"]))
        data.update(
            self._validate_session(
                data["access_token"],
                data["session_id"],
                data["request_id"],
                data["identifier"],
            )
        )
        session.update(data)
        session["comdirect_import_step"] = "login_started"
        # wait for user to validate the tan then call complete_login_flow

    def complete_login_flow(self, session: SessionBase):
        data = {
            "access_token": session["access_token"],
            "session_id": session["session_id"],
            "request_id": session["request_id"],
            "identifier": session["identifier"],
            "challenge_id": session["challenge_id"],
            "refresh_token": session["refresh_token"],
        }
        self._activate_session(
            data["access_token"],
            data["session_id"],
            data["request_id"],
            data["identifier"],
            data["challenge_id"],
        )
        data.update(self._get_api_tokens(data["access_token"]))
        session.update(data)
        session["comdirect_import_step"] = "login_completed"

    def _refresh(self, session: SessionBase):
        data = self._refresh_tokens(session["api_refresh_token"])
        session.update(data)

    def reset(self, session: SessionBase):
        del session["comdirect_import_step"]
        del session["access_token"]
        del session["refresh_token"]
        del session["identifier"]
        del session["session_id"]
        del session["request_id"]
        del session["challenge_id"]
        del session["api_access_token"]
        del session["api_refresh_token"]

    class Amount(BaseModel):
        value: Decimal
        unit: str

    class Remitter(BaseModel):
        holderName: str = ""

    class Transaction(BaseModel):
        reference: str
        bookingStatus: Literal["NOTBOOKED", "BOOKED"]
        bookingDate: date | None
        amount: "ComdirectImport.Amount"
        remittanceInfo: str
        remitter: Union["ComdirectImport.Remitter", None]

        def get_description(self) -> str:
            if self.remitter and self.remitter.holderName:
                return self.remitter.holderName
            if self.remittanceInfo:
                return self.remittanceInfo
            return self.reference

    class Transactions(BaseModel):
        paging: dict
        aggregated: dict
        values: list["ComdirectImport.Transaction"]

    def import_transactions(self, session: SessionBase, page: int = 0) -> date | None:
        self._refresh(session)
        raw_data = self.get_transactions(
            session["api_access_token"],
            session["session_id"],
            session["request_id"],
            page,
        )
        data = self.Transactions.model_validate(raw_data)
        existing = set(self.changes.values_list("sha", flat=True))
        changes = []
        earliest_change_date: date | None = None
        for transaction in data.values:
            if earliest_change_date is None:
                earliest_change_date = transaction.bookingDate
            elif (
                transaction.bookingDate
                and transaction.bookingDate < earliest_change_date
            ):
                earliest_change_date = transaction.bookingDate
            if transaction.bookingStatus != "BOOKED":
                continue
            change = ComdirectImportChange(
                comdirect_import=self,
                date=transaction.bookingDate,
                description=transaction.get_description(),
                change=transaction.amount.value,
            )
            change.sha = change.calculate_sha()
            if change.sha in existing:
                continue
            changes.append(change)
        ComdirectImportChange.objects.bulk_create(changes)
        session["comdirect_import_step"] = "import_completed"
        return earliest_change_date


class ComdirectImportChange(models.Model):
    comdirect_import = models.ForeignKey(
        ComdirectImport,
        on_delete=models.CASCADE,
        related_name="changes",
    )
    sha = models.CharField(max_length=64)
    date = models.DateField()
    description = models.TextField()
    change = models.DecimalField(decimal_places=2, max_digits=15)
    is_deleted = models.BooleanField(default=False)

    linked_change = models.ForeignKey(
        Change,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comdirect_import_changes",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Comdirect Import Change"
        verbose_name_plural = "Comdirect Import Changes"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"Comdirect Change for {self.comdirect_import.account.name}"

    def calculate_sha(self):
        sha_str = f"{self.date}-{self.description}-{self.change}"
        return hashlib.sha256(sha_str.encode("utf-8")).hexdigest()

    @property
    def description_str(self):
        if len(str(self.description)) > 35:
            return self.description[:35] + "..."
        return self.description

    def import_into_account(self, category: Category):
        if self.linked_change is not None:
            raise ValueError("change is already imported")
        change = Change(
            account=self.comdirect_import.account,
            date=datetime.combine(self.date, datetime.min.time()),
            category=category,
            description=self.description,
            change=self.change,
        )
        self.linked_change = change
        return change
