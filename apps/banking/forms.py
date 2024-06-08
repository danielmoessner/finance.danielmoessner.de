from datetime import datetime

from django import forms
from django.db import transaction

from apps.banking.models import Account, Category, Change, Depot


# depot
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


# account
class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = (
            "name",
            "bucket",
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


# category
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = (
            "name",
            "description",
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


# change
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
        self.fields["category"].queryset = depot.categories.all()
        self.fields["date"].initial = datetime.now()
        self.fields["description"].widget.attrs.update({"class": "small"})


class MoveMoneyForm(forms.Form):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
        label="Date",
    )
    from_account = forms.ModelChoiceField(widget=forms.Select, queryset=None)
    to_account = forms.ModelChoiceField(widget=forms.Select, queryset=None)
    change = ChangeField()

    def __init__(self, depot, *args, **kwargs):
        super(MoveMoneyForm, self).__init__(*args, **kwargs)
        self.fields["from_account"].queryset = depot.accounts.all()
        self.fields["to_account"].queryset = depot.accounts.all()
        self.fields["date"].initial = datetime.now()

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("from_account") == cleaned_data.get("to_account"):
            raise forms.ValidationError("The accounts must be different.")
        return cleaned_data

    def save(self, commit=True):
        from_account = self.cleaned_data.get("from_account")
        to_account = self.cleaned_data.get("to_account")
        change = self.cleaned_data.get("change")
        date = self.cleaned_data.get("date")
        description = f"From {from_account} to {to_account}"
        category, _ = Category.objects.get_or_create(name="Money Movement")
        with transaction.atomic():
            Change.objects.create(
                account=from_account,
                date=date,
                change=-change,
                description=description,
                category=category,
            )
            Change.objects.create(
                account=to_account,
                date=date,
                change=change,
                description=description,
                category=category,
            )
        return True
