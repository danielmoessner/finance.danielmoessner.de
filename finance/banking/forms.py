from django import forms

from finance.banking.models import Depot
from finance.banking.models import Change
from finance.banking.models import Account
from finance.banking.models import Category
from finance.banking.models import Timespan

from datetime import datetime
import pytz


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


# ACCOUNT
class CreateAccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = (
            "name",
        )


class UpdateAccountForm(forms.ModelForm):
    pk = forms.IntegerField(min_value=0)

    class Meta:
        model = Account
        fields = (
            "name",
            "pk"
        )


# CATEGORY
class CreateCategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = (
            "name",
            "description",
        )


class UpdateCategoryForm(forms.ModelForm):
    pk = forms.IntegerField(min_value=0)

    class Meta:
        model = Category
        fields = (
            "pk",
            "name",
            "description",
        )


# CHANGE
class CreateChangeForm(forms.ModelForm):
    date = forms.CharField(max_length=16, min_length=16)

    class Meta:
        model = Change
        fields = (
            "account",
            "date",
            "category",
            "description",
            "change"
        )

    def clean_date(self):
        date = self.cleaned_data["date"]
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M').replace(tzinfo=pytz.utc)
        return date


class UpdateChangeForm(forms.ModelForm):
    pk = forms.IntegerField(min_value=0)
    date = forms.CharField(max_length=16, min_length=16)

    class Meta:
        model = Change
        fields = (
            "pk",
            "account",
            "date",
            "category",
            "description",
            "change"
        )

    def clean_date(self):
        date = self.cleaned_data["date"]
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M').replace(tzinfo=pytz.utc)
        return date


# TIMESPAN
class CreateTimespanForm(forms.ModelForm):
    start_date = forms.CharField(max_length=16, min_length=16)
    end_date = forms.CharField(max_length=16, min_length=16)

    class Meta:
        model = Timespan
        fields = (
            "name",
            "start_date",
            "end_date"
        )

    def clean_start_date(self):
        start_date = self.cleaned_data["start_date"]
        start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M').replace(tzinfo=pytz.utc)
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data["end_date"]
        end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M').replace(tzinfo=pytz.utc)
        return end_date


class UpdateActiveOnTimespanForm(forms.ModelForm):
    pk = forms.IntegerField(min_value=0)

    class Meta:
        model = Timespan
        fields = (
            "pk",
        )
