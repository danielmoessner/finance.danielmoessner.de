import json
from datetime import datetime

import pandas as pd
from django import forms
from django.contrib.sessions.backends.base import SessionBase
from django.db import transaction
from django.utils import timezone

from apps.banking.models import (
    Account,
    Category,
    Change,
    ComdirectImport,
    ComdirectImportChange,
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


class ImportForm(forms.Form):
    account = forms.ModelChoiceField(widget=forms.Select, queryset=None)
    mapping = forms.CharField(
        widget=forms.Textarea, label="Category Mapping", required=True
    )
    file = forms.FileField(label="CSV File")

    class Meta:
        fields = (
            "mapping",
            "account",
            "file",
        )

    def __init__(self, depot, *args, **kwargs):
        super(ImportForm, self).__init__(*args, **kwargs)
        self.fields["account"].queryset = depot.accounts.all()
        if not self.is_bound:
            initial_account = kwargs.get("initial", {}).get("account", None)
            assert initial_account is not None
            account = depot.accounts.get(pk=initial_account)
            self.import_map, _ = account.import_maps.get_or_create(
                defaults={"map": "{}"}
            )
            self.fields["mapping"].initial = self.import_map.map

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
            if category_name not in self.cleaned_data["mapping"]:
                raise forms.ValidationError(
                    f"Category '{category_name}' not in mapping."
                )
        return df

    def save(self, *args, **kwargs):
        df = self.cleaned_data["file"]
        mapping_str = self.cleaned_data["mapping"]
        account = self.cleaned_data["account"]
        import_map = account.import_maps.first()
        import_map.map = mapping_str
        import_map.save()
        category_mapping = json.loads(mapping_str)
        category_map = {c.name: c for c in account.depot.categories.all()}
        changes = []
        for row in df.itertuples(index=False):
            date = getattr(row, "Datum")
            category_name = getattr(row, "Kategorie")
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
        account.changes.all().delete()
        Change.objects.bulk_create(changes)


class ComdirectStartLoginForm(forms.ModelForm):
    instance: ComdirectImport

    class Meta:
        model = ComdirectImport
        fields = ()

    def __init__(self, depot: Depot, session: SessionBase, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

    def save(self, commit: bool = True):
        self.instance.start_login_flow(self.session)
        return self.instance


class ComdirectCompleteLoginForm(forms.ModelForm):
    instance: ComdirectImport

    class Meta:
        model = ComdirectImport
        fields = ()

    def __init__(self, depot: Depot, session: SessionBase, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

    def save(self, commit: bool = True):
        self.instance.complete_login_flow(self.session)
        return self.instance


class ComdirectImportChangesForm(forms.ModelForm):
    instance: ComdirectImport

    class Meta:
        model = ComdirectImport
        fields = ()

    def __init__(self, depot: Depot, session: SessionBase, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

    def save(self, commit: bool = True):
        self.instance.import_transactions(self.session)
        return self.instance


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
