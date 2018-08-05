from django.db.models import Q
from django import forms

from finance.core.utils import create_slug
from .models import Transaction
from .models import Timespan
from .models import Account
from .models import Asset
from .models import Trade
from .models import Depot

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


# asset
class AssetSelectForm(forms.Form):
    asset = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = (
            "asset",
        )

    def __init__(self, depot, *args, **kwargs):
        super(AssetSelectForm, self).__init__(*args, **kwargs)
        self.depot = depot
        self.fields["asset"].queryset = Asset.objects.exclude(symbol=None)

    def clean(self):
        depot = self.depot
        asset = self.cleaned_data["asset"]
        if Trade.objects.filter(Q(buy_asset=asset) | Q(sell_asset=asset),
                                account__in=depot.accounts.all()).exists():
            raise forms.ValidationError(
                "You can't select this asset, because there still exist trades with that asset.")
        if Transaction.objects.filter(Q(from_account__in=depot.accounts.all()) | Q(
                to_account__in=depot.accounts.all()), asset=asset).exists():
            raise forms.ValidationError(
                "You can't select this asset, because there still exist transaction with that "
                "asset.")


# trade
class TradeForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"},
                                                          format="%Y-%m-%dT%H:%M"),
                               input_formats=["%Y-%m-%dT%H:%M"], label="Date")

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

    def __init__(self, depot, *args, **kwargs):
        super(TradeForm, self).__init__(*args, **kwargs)
        self.fields["account"].queryset = depot.accounts.all()
        self.fields["buy_asset"].queryset = depot.assets.all()
        self.fields["sell_asset"].queryset = depot.assets.all()
        self.fields["fees_asset"].queryset = depot.assets.all()
        self.fields["date"].initial = datetime.now()


# transaction
class TransactionForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"},
                                                          format="%Y-%m-%dT%H:%M"),
                               input_formats=["%Y-%m-%dT%H:%M"], label="Date")

    class Meta:
        model = Transaction
        fields = (
            "asset",
            "date",
            "from_account",
            "to_account",
            "amount",
            "fees",
        )

    def __init__(self, depot, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)
        self.fields["asset"].queryset = depot.assets.all()
        self.fields["from_account"].queryset = depot.accounts.all()
        self.fields["to_account"].queryset = depot.accounts.all()
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
