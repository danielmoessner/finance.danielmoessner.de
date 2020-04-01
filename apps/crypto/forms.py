from django.utils import timezone
from django import forms

from .models import Account, Flow, Transaction, Timespan, Trade, Depot

from datetime import datetime


# depot
class DepotForm(forms.ModelForm):
    class Meta:
        model = Depot
        fields = (
            "name",
        )

    def __init__(self, user, *args, **kwargs):
        super(DepotForm, self).__init__(*args, **kwargs)
        self.instance.user = user


class DepotSelectForm(forms.Form):
    depot = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = (
            "depot",
        )

    def __init__(self, user, *args, **kwargs):
        super(DepotSelectForm, self).__init__(*args, **kwargs)
        self.fields["depot"].queryset = user.crypto_depots.all()


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
        )

    def __init__(self, depot, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        self.instance.depot = depot


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
        self.fields["asset"].queryset = depot.assets.all()


# trade
class TradeForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
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
        )

    def __init__(self, depot, *args, **kwargs):
        super(TradeForm, self).__init__(*args, **kwargs)
        self.fields["account"].queryset = depot.accounts.order_by("name")
        self.fields["buy_asset"].queryset = depot.assets.order_by("symbol")
        self.fields["sell_asset"].queryset = depot.assets.order_by("symbol")
        self.fields["date"].initial = datetime.now()

    def clean(self):
        account = self.cleaned_data['account']
        sell_asset = self.cleaned_data['sell_asset']
        sell_amount = self.cleaned_data['sell_amount']
        buy_amount = self.cleaned_data['buy_amount']
        date = self.cleaned_data['date']
        # check that buy and sell amount is positive because a trade doesnt make sense otherwise
        if sell_amount < 0 or buy_amount < 0:
            raise forms.ValidationError('Sell and buy amount must be positive.')
        # check that enough asset is available of the asset that is sold
        if account.get_amount_asset_before_date(sell_asset, date) < sell_amount:
            raise forms.ValidationError('There is not enough asset on this account to support this trade.')


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
        self.fields["asset"].queryset = depot.assets.order_by("symbol")
        self.fields["from_account"].queryset = depot.accounts.order_by("name")
        self.fields["to_account"].queryset = depot.accounts.order_by("name")
        self.fields["date"].initial = datetime.now()

    def clean(self):
        from_account = self.cleaned_data['from_account']
        asset = self.cleaned_data['asset']
        amount = self.cleaned_data['amount']
        fees = self.cleaned_data['fees']
        date = self.cleaned_data['date']
        # check that buy and sell amount is positive because a trade doesnt make sense otherwise
        if amount < 0:
            raise forms.ValidationError('The amount must be positive.')
        # check that enough asset is available of the asset that is sold
        if from_account.get_amount_asset_before_date(asset, date) < (amount + fees):
            raise forms.ValidationError('There is not enough asset on this account to support this transaction.')


# flow
class FlowForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.DateTimeInput(
        attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        input_formats=['%Y-%m-%dT%H:%M'], label='Date')

    class Meta:
        model = Flow
        fields = (
            'account',
            'date',
            'flow',
        )

    def __init__(self, depot, *args, **kwargs):
        super(FlowForm, self).__init__(*args, **kwargs)
        self.instance.asset = depot.assets.get(symbol='EUR')
        self.fields['account'].queryset = depot.accounts.all()
        self.fields['date'].initial = timezone.now().date

    def clean(self):
        date = self.cleaned_data['date']
        flow = self.cleaned_data['flow']
        account = self.cleaned_data['account']
        asset = self.instance.asset
        # check that enough asset is available if asset is withdrawn
        if flow < 0 and account.get_amount_asset_before_date(asset, date) < abs(flow):
            raise forms.ValidationError('There is not enough asset on this account to support this flow.')


# timespan
class TimespanForm(forms.ModelForm):
    start_date = forms.DateTimeField(widget=forms.DateTimeInput(
        attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M"], label="Start Date (not required)", required=False)
    end_date = forms.DateTimeField(widget=forms.DateTimeInput(
        attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M"], label="End Date (not required)", required=False)

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
