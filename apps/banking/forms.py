import json
from datetime import datetime, timedelta

import pandas as pd
from django import forms
from django.contrib.sessions.backends.base import SessionBase
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.banking.models import (
    Account,
    Category,
    Change,
    ComdirectImport,
    ComdirectImportChange,
    CsvImport,
    Depot,
)


class DepotForm(forms.ModelForm):
    class Meta:
        model = Depot
        fields = ("name",)

    def __init__(self, user, *args, **kwargs):
        super(DepotForm, self).__init__(*args, **kwargs)
        self.instance.user = user


class DepotSelectForm(forms.Form):
    depot = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = ("depot",)

    def __init__(self, user, *args, **kwargs):
        super(DepotSelectForm, self).__init__(*args, **kwargs)
        self.fields["depot"].queryset = user.banking_depots.all()


class DepotActiveForm(forms.ModelForm):
    class Meta:
        model = Depot
        fields = ("is_active",)


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = (
            "name",
            "bucket",
            "is_archived",
            "default_date",
        )

    def __init__(self, depot: Depot, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        self.instance.depot = depot
        self.fields["bucket"].queryset = depot.user.buckets.all()


class AccountSelectForm(forms.Form):
    account = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = ("account",)

    def __init__(self, depot: Depot, *args, **kwargs):
        super(AccountSelectForm, self).__init__(*args, **kwargs)
        self.fields["account"].queryset = depot.accounts.all()


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = (
            "name",
            "description",
            "monthly_budget",
            "is_archived",
        )

    def __init__(self, depot, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        self.instance.depot = depot


class CategorySelectForm(forms.Form):
    category = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = ("category",)

    def __init__(self, depot, *args, **kwargs):
        super(CategorySelectForm, self).__init__(*args, **kwargs)
        self.fields["category"].queryset = depot.categories.all()


class ChangeField(forms.DecimalField):
    def __init__(self, *args, **kwargs):
        attrs = {
            "pattern": r"-?\d+(.|,)?\d{0,2}",
            "title": "A number with 2 decimal places.",
        }
        super().__init__(widget=forms.TextInput(attrs=attrs), *args, **kwargs)

    def to_python(self, value):
        if isinstance(value, str):
            value = value.replace(",", ".")
        return super().to_python(value)


class ChangeForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
        label="Date",
    )
    change = ChangeField()

    class Meta:
        model = Change
        fields = (
            "account",
            "date",
            "change",
            "category",
            "description",
        )

    def __init__(self, depot, *args, **kwargs):
        super(ChangeForm, self).__init__(*args, **kwargs)
        self.fields["account"].queryset = depot.accounts.all()
        self.fields["category"].queryset = depot.categories.order_by("-changes_count")
        self.fields["date"].initial = datetime.now()
        account_pk = kwargs.get("initial", {}).get("account", 0)
        if account_pk:
            account = depot.accounts.filter(pk=account_pk).first()
            if account and account.default_date == "last_transaction":
                last_change = account.changes.order_by("-date").first()
                if last_change:
                    default_date = last_change.date
                    now = timezone.now()
                    default_date = default_date.replace(
                        hour=now.hour, minute=now.minute, second=0, microsecond=0
                    )
                    self.fields["date"].initial = default_date
        self.fields["description"].widget.attrs.update({"class": "small"})


class CombineChangeForm(forms.Form):
    SEPARATOR_VALUE = "__current_change_separator__"

    other_change = forms.ChoiceField(
        widget=forms.Select,
        choices=[],
        label="Combine with",
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, depot: Depot, primary_change: Change, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.depot = depot
        self.primary_change = primary_change
        past_ids, future_ids = self._get_neighboring_change_ids()
        neighboring_ids = list(reversed(future_ids)) + past_ids
        neighboring_changes = Change.objects.filter(pk__in=neighboring_ids)
        self._neighboring_changes_by_id = {
            str(change.pk): change for change in neighboring_changes
        }

        choices = [
            (
                str(change_id),
                self._change_option_label(
                    self._neighboring_changes_by_id[str(change_id)]
                ),
            )
            for change_id in reversed(future_ids)
            if str(change_id) in self._neighboring_changes_by_id
        ]
        if past_ids and future_ids:
            choices.append(
                (
                    self.SEPARATOR_VALUE,
                    "----- Current Change (not selectable) -----",
                )
            )
        choices.extend(
            [
                (
                    str(change_id),
                    self._change_option_label(
                        self._neighboring_changes_by_id[str(change_id)]
                    ),
                )
                for change_id in past_ids
                if str(change_id) in self._neighboring_changes_by_id
            ]
        )
        self.fields["other_change"].choices = choices
        self.fields["description"].initial = primary_change.description

    def _get_base_queryset(self):
        return Change.objects.filter(
            account=self.primary_change.account,
            category=self.primary_change.category,
            account__depot=self.depot,
        ).exclude(pk=self.primary_change.pk)

    def _get_neighboring_change_ids(self) -> tuple[list[int], list[int]]:
        base_queryset = self._get_base_queryset()

        past_ids = list(
            base_queryset.filter(
                Q(date__lt=self.primary_change.date)
                | Q(date=self.primary_change.date, pk__lt=self.primary_change.pk)
            )
            .order_by("-date", "-pk")
            .values_list("pk", flat=True)[:15]
        )
        future_ids = list(
            base_queryset.filter(
                Q(date__gt=self.primary_change.date)
                | Q(date=self.primary_change.date, pk__gt=self.primary_change.pk)
            )
            .order_by("date", "pk")
            .values_list("pk", flat=True)[:15]
        )

        return past_ids, future_ids

    def _change_option_label(self, change: Change) -> str:
        description = change.description or ""
        if len(description) > 80:
            description = f"{description[:80]}..."
        return (
            f"{change.date.strftime('%d.%m.%Y %H:%M')}"
            f" | {change.change} | {description}"
        )

    def clean(self):
        cleaned_data = super().clean()
        selected_change_id = cleaned_data.get("other_change")
        if not selected_change_id:
            return cleaned_data

        if selected_change_id == self.SEPARATOR_VALUE:
            self.add_error("other_change", "Please select a change.")
            return cleaned_data

        other_change = self._neighboring_changes_by_id.get(selected_change_id)
        if other_change is None:
            self.add_error("other_change", "Please select a valid neighboring change.")
            return cleaned_data

        if other_change.account_id != self.primary_change.account_id:
            self.add_error("other_change", "Selected change must belong to the same account.")
            return cleaned_data
        if other_change.category_id != self.primary_change.category_id:
            self.add_error("other_change", "Selected change must belong to the same category.")
            return cleaned_data

        cleaned_data["other_change"] = other_change
        return cleaned_data

    def save(self, commit: bool = True):
        other_change = self.cleaned_data["other_change"]
        description = self.cleaned_data.get("description", "")
        if description == "":
            description = self.primary_change.description

        with transaction.atomic():
            combined_change = Change.objects.create(
                account=self.primary_change.account,
                date=self.primary_change.date,
                category=self.primary_change.category,
                change=self.primary_change.change + other_change.change,
                description=description,
            )
            self.primary_change.delete()
            other_change.delete()

        return combined_change


class CsvImportForm(forms.ModelForm):
    map = forms.CharField(
        widget=forms.Textarea, label="Category Mapping", required=True
    )
    file = forms.FileField(label="CSV File")
    instance: CsvImport

    class Meta:
        model = CsvImport
        fields = (
            "map",
            "file",
        )

    def __init__(self, depot: Depot, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_file(self):
        file = self.cleaned_data["file"]
        if not file.name.endswith(".csv"):
            raise forms.ValidationError("Only CSV files are supported.")
        if file.size > 5 * 1024 * 1024:
            raise forms.ValidationError("File size exceeds 5MB.")
        df = pd.read_csv(file)
        if df.empty:
            raise forms.ValidationError("The CSV file is empty.")
        df.columns = df.columns.str.strip()
        required_columns = {"Datum", "Kategorie", "Beschreibung", "Cashflow"}
        if not required_columns.issubset(df.columns):
            raise forms.ValidationError(
                f"The CSV file must contain the following columns: {', '.join(required_columns)}."
            )
        df = df.dropna(subset=["Cashflow"])
        categories = df["Kategorie"].unique()
        for category_name in categories:
            if category_name not in self.cleaned_data["map"]:
                raise forms.ValidationError(f"Category '{category_name}' not in map.")
        return df

    def save(self, *args, **kwargs):
        df = self.cleaned_data["file"]
        map_str = self.cleaned_data["map"]
        account = self.instance.account
        csv_import = account.csv_import or CsvImport(account=account)
        csv_import.map = map_str
        csv_import.save()
        category_mapping = json.loads(map_str)
        category_map: dict[str, Category] = {
            c.name: c for c in account.depot.categories.all()
        }
        changes = []
        for row in df.itertuples(index=False):
            date = getattr(row, "Datum")
            category_name: str = getattr(row, "Kategorie")
            description = getattr(row, "Beschreibung")
            amount = getattr(row, "Cashflow")
            date = datetime.strptime(date, "%d.%m.%Y").replace(
                hour=12, minute=0, tzinfo=timezone.get_current_timezone()
            )
            change_amount = float(
                str(amount)
                .replace("€", "")
                .replace(".", "")
                .replace(",", ".")
                .replace(" ", "")
            )
            category = category_map[category_mapping[category_name]]
            changes.append(
                Change(
                    account=account,
                    date=date,
                    change=change_amount,
                    category=category,
                    description=description,
                )
            )
        with transaction.atomic():
            account.changes.all().delete()
            Change.objects.bulk_create(changes)
        account.depot.set_balances_to_none()


class ComdirectStartLoginForm(forms.ModelForm):
    instance: ComdirectImport
    text = "Click submit to start the login process."

    class Meta:
        model = ComdirectImport
        fields = ()

    def __init__(self, depot: Depot, session: SessionBase, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

    def is_valid(self):
        try:
            self.instance.start_login_flow(self.session)
        except Exception as e:
            self.errors["__all__"] = self.error_class([str(e)])
            return False
        return True


class ComdirectCompleteLoginForm(forms.ModelForm):
    instance: ComdirectImport
    text = "Please validate the tan and submit again."

    class Meta:
        model = ComdirectImport
        fields = ()

    def __init__(self, depot: Depot, session: SessionBase, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

    def is_valid(self):
        try:
            self.instance.complete_login_flow(self.session)
        except Exception as e:
            self.errors["__all__"] = self.error_class([str(e)])
            return False
        return True


class ComdirectImportChangesForm(forms.ModelForm):
    instance: ComdirectImport
    text = "The login was successful please submit again to import the changes."

    class Meta:
        model = ComdirectImport
        fields = ()

    def __init__(self, depot: Depot, session: SessionBase, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

    def is_valid(self):
        latest_change = self.instance.changes.order_by("-date").first()
        if latest_change is None:
            latest = timezone.now().date() - timedelta(days=14)
        else:
            latest = latest_change.date
        page = 0
        while True:
            try:
                earliest = self.instance.import_transactions(self.session, page=page)
            except Exception as e:
                self.instance.reset(self.session)
                self.errors["__all__"] = self.error_class([str(e)])
                return False
            if earliest is None:
                break
            if earliest < latest:
                break
            page += 1
        return True


class ImportComdirectChange(forms.ModelForm):
    instance: ComdirectImportChange
    category = forms.ModelChoiceField(
        widget=forms.Select, queryset=Category.objects.none(), required=True
    )
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
        label="Date",
    )

    class Meta:
        model = ComdirectImportChange
        fields = ("date", "change", "category", "description")

    def __init__(self, depot: Depot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = depot.categories.all()
        self.fields["change"].disabled = True
        self.fields["date"].disabled = True

    def save(self, commit: bool = True):
        change = self.instance.import_into_account(self.cleaned_data["category"])
        with transaction.atomic():
            change.save()
            self.instance.save()
        return self.instance


class DeleteComdirectChange(forms.ModelForm):
    instance: ComdirectImportChange

    class Meta:
        model = ComdirectImportChange
        fields = ()

    def __init__(self, depot: Depot, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, commit: bool = True):
        self.instance.is_deleted = True
        self.instance.save()
        return self.instance
