from datetime import datetime

from django import forms
from django.utils import timezone

from apps.banking.models import Account, Category, Change, Depot


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
