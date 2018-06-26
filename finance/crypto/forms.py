from django import forms

from finance.core.utils import create_slug
from .models import Depot
from .models import Asset
from .models import Trade
from .models import Price
from .models import Account
from .models import Timespan
from .models import Transaction

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


# ASSET
class ConnectDepotAssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = (
            "symbol",
        )


class CreatePrivateAssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = (
            "private_name",
            "private_symbol"
        )

    def clean_private_name(self):
        data = self.cleaned_data["private_name"]
        if data is None:
            raise forms.ValidationError("The name of the asset must not be left empty.")
        return data

    def clean_private_symbol(self):
        data = self.cleaned_data["private_symbol"]
        if data is None:
            raise forms.ValidationError("The symbol of the asset must not be left empty.")
        data = str(data).upper()
        return data

    def save(self, commit=True):
        asset = super(CreatePrivateAssetForm, self).save(commit=False)
        asset.slug = create_slug(asset, on=asset.private_name)
        asset.save()
        return asset


class UpdatePrivateAssetForm(forms.ModelForm):
    pk = forms.IntegerField(min_value=0)

    class Meta:
        model = Asset
        fields = (
            "private_name",
            "private_symbol",
            "pk"
        )


# TRADE
class CreateTradeForm(forms.ModelForm):
    date = forms.CharField(max_length=16, min_length=16)

    class Meta:
        model = Trade
        fields = (
            "account",
            "date",
            "buy_amount",
            "buy_asset",
            "sell_amount",
            "sell_asset",
            "fees",
            "fees_asset"
        )

    def clean_date(self):
        date = self.cleaned_data["date"]
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M').replace(tzinfo=pytz.utc)
        return date


class UpdateTradeForm(forms.ModelForm):
    pk = forms.IntegerField(min_value=0)
    date = forms.CharField(max_length=16, min_length=16)

    class Meta:
        model = Trade
        fields = (
            "pk",
            "account",
            "date",
            "buy_amount",
            "buy_asset",
            "sell_amount",
            "sell_asset",
            "fees",
            "fees_asset"
        )

    def clean_date(self):
        date = self.cleaned_data["date"]
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M').replace(tzinfo=pytz.utc)
        return date


# TRANSACTION
class CreateTransactionForm(forms.ModelForm):
    date = forms.CharField(max_length=16, min_length=16)

    class Meta:
        model = Transaction
        fields = (
            "asset",
            "from_account",
            "to_account",
            "date",
            "amount",
            "fees",
        )

    def clean_date(self):
        date = self.cleaned_data["date"]
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M').replace(tzinfo=pytz.utc)
        return date


class UpdateTransactionForm(forms.ModelForm):
    pk = forms.IntegerField(min_value=0)
    date = forms.CharField(max_length=16, min_length=16)

    class Meta:
        model = Transaction
        fields = (
            "asset",
            "from_account",
            "to_account",
            "date",
            "amount",
            "fees",
        )

    def clean_date(self):
        date = self.cleaned_data["date"]
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M').replace(tzinfo=pytz.utc)
        return date


# PRICE
class CreatePriceForm(forms.ModelForm):
    date = forms.CharField(max_length=16, min_length=16)

    class Meta:
        model = Price
        fields = (
            "price",
            "date"
        )

    def clean_date(self):
        date = self.cleaned_data["date"]
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M').replace(tzinfo=pytz.utc)
        return date


class EditPriceForm(forms.ModelForm):
    pk = forms.IntegerField(min_value=0)
    date = forms.CharField(max_length=16, min_length=16)

    class Meta:
        model = Price
        fields = (
            "price",
            "date"
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
