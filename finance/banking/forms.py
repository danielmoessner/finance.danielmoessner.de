from django import forms

from finance.banking.models import Timespan
from finance.banking.models import Category
from finance.banking.models import Account
from finance.banking.models import Change
from finance.banking.models import Depot
from finance.core.utils import create_slug

from datetime import datetime


# DEPOT
class CreateDepotForm(forms.ModelForm):
    class Meta:
        model = Depot
        fields = (
            "name",
        )


class UpdateDepotForm(forms.ModelForm):
    pk = forms.IntegerField(min_value=0)

    class Meta:
        model = Depot
        fields = (
            "name",
            "pk",
        )


# account
class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = (
            "name",
        )

    def __init__(self, depot, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        self.instance.depot = depot

    def save(self, commit=True):
        self.instance.slug = create_slug(self.instance, self.instance.name)
        return super(AccountForm, self).save(commit=commit)


class AccountSelectForm(forms.Form):
    account = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = (
            "account",
        )

    def __init__(self, depot, *args, **kwargs):
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

    def save(self, commit=True):
        self.instance.slug = create_slug(self.instance, self.instance.name)
        return super(CategoryForm, self).save(commit=commit)


class CategorySelectForm(forms.Form):
    category = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = (
            "category",
        )

    def __init__(self, depot, *args, **kwargs):
        super(CategorySelectForm, self).__init__(*args, **kwargs)
        self.fields["category"].queryset = depot.categories.all()


# change
class ChangeForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"},
                                                          format="%Y-%m-%dT%H:%M"),
                               input_formats=["%Y-%m-%dT%H:%M"], label="Date")

    class Meta:
        model = Change
        fields = (
            "account",
            "date",
            "category",
            "description",
            "change"
        )

    def __init__(self, depot, *args, **kwargs):
        super(ChangeForm, self).__init__(*args, **kwargs)
        self.fields["account"].queryset = depot.accounts.all()
        self.fields["category"].queryset = depot.categories.all()
        self.fields["date"].initial = datetime.now()


# timespan
class TimespanForm(forms.ModelForm):
    start_date = forms.DateTimeField(widget=forms.DateTimeInput(
        attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M"], label="Date")
    end_date = forms.DateTimeField(widget=forms.DateTimeInput(
        attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M"], label="Date")

    class Meta:
        model = Timespan
        fields = (
            "name",
            "start_date",
            "end_date"
        )

    def __init__(self, depot, *args, **kwargs):
        super(TimespanForm, self).__init__(*args, **kwargs)
        self.instance.depot = depot


class TimespanActiveForm(forms.ModelForm):
    class Meta:
        model = Timespan
        fields = ("is_active",)

    def __init__(self, depot, *args, **kwargs):
        super(TimespanActiveForm, self).__init__(*args, **kwargs)
        depot.timespans.update(is_active=False)
