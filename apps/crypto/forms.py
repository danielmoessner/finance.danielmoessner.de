from datetime import datetime

from django import forms
from django.db.models import Q
from django.utils import timezone

from apps.core.fetchers.website import WebsiteFetcherInput
from apps.crypto.fetchers.coingecko import CoinGeckoFetcherInput

from .models import Account, Asset, Depot, Flow, Price, PriceFetcher, Trade, Transaction


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
        self.fields["depot"].queryset = user.crypto_depots.all()


class DepotActiveForm(forms.ModelForm):
    class Meta:
        model = Depot
        fields = ("is_active",)


# account
class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ("name",)

    def __init__(self, depot, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        self.instance.depot = depot


class AccountSelectForm(forms.Form):
    account = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = ("account",)

    def __init__(self, depot, *args, **kwargs):
        super(AccountSelectForm, self).__init__(*args, **kwargs)
        self.fields["account"].queryset = depot.accounts.all()


# asset
class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ("symbol",)
        help_texts = {
            "symbol": (
                "It's not advised to change the symbol of"
                " an asset as the prices of the asset will change."
            ),
        }

    def __init__(self, depot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.depot = depot


class AssetSelectForm(forms.Form):
    asset = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = ("asset",)

    def __init__(self, depot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asset"].queryset = depot.assets.all()


# trade
class TradeForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
        label="Date",
    )

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
        if (
            "account" not in self.cleaned_data
            or "sell_asset" not in self.cleaned_data
            or "sell_amount" not in self.cleaned_data
            or "buy_amount" not in self.cleaned_data
            or "date" not in self.cleaned_data
        ):
            return
        account = self.cleaned_data["account"]
        sell_asset = self.cleaned_data["sell_asset"]
        sell_amount = self.cleaned_data["sell_amount"]
        buy_amount = self.cleaned_data["buy_amount"]
        date = self.cleaned_data["date"]
        # check that there is not already a transaction or
        # flow on this exact date and account
        if Transaction.objects.filter(
            Q(date=date), Q(from_account=account) | Q(to_account=account)
        ).exists():
            raise forms.ValidationError(
                "There is already a transaction at this date and account."
            )
        if Flow.objects.filter(date=date, account=account).exists():
            raise forms.ValidationError(
                "There is already a flow at this date and account"
            )
        # check that buy and sell amount is positive because a
        # trade doesnt make sense otherwise
        if sell_amount < 0 or buy_amount < 0:
            raise forms.ValidationError("Sell and buy amount must be positive.")
        # check that enough asset is available of the asset that is sold
        # TODO exclude the own instance from the available calculation
        available_amount = account.get_amount_asset_before_date(sell_asset, date)
        if available_amount < sell_amount:
            message = (
                "There is not enough asset on this account to support this trade. "
                "There is {} available.".format(available_amount)
            )
            raise forms.ValidationError(message)


# transaction
class TransactionForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
        label="Date",
    )

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
        from_account = self.cleaned_data["from_account"]
        to_account = self.cleaned_data["to_account"]
        asset = self.cleaned_data["asset"]
        amount = self.cleaned_data["amount"]
        fees = self.cleaned_data["fees"]
        date = self.cleaned_data["date"]
        # check that there is not already a trade or flow on this exact date and account
        if Trade.objects.filter(
            Q(date=date), Q(account=from_account) | Q(account=to_account)
        ).exists():
            raise forms.ValidationError(
                "There is already a trade at this date and one of the accounts."
            )
        if Flow.objects.filter(
            Q(date=date), Q(account=from_account) | Q(account=to_account)
        ).exists():
            raise forms.ValidationError(
                "There is already a flow at this date and account"
            )
        # check that buy and sell amount is positive because
        # a trade doesnt make sense otherwise
        if amount < 0:
            raise forms.ValidationError("The amount must be positive.")
        # check that enough asset is available of the asset that is sold
        exclude = [self.instance.pk] if self.instance.pk else None
        available_amount = from_account.get_amount_asset_before_date(
            asset, date, exclude_transactions=exclude
        )
        if available_amount < (amount + fees):
            message = (
                "There is not enough asset on this account"
                " to support this transaction. "
                "There is {} available".format(available_amount)
            )
            raise forms.ValidationError(message)


# flow
class FlowForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
        label="Date",
    )

    class Meta:
        model = Flow
        fields = (
            "account",
            "date",
            "flow",
        )

    def __init__(self, depot, *args, **kwargs):
        super(FlowForm, self).__init__(*args, **kwargs)
        self.instance.asset = depot.assets.get(symbol="EUR")
        self.fields["account"].queryset = depot.accounts.all()
        self.fields["date"].initial = timezone.now().date

    def clean(self):
        date = self.cleaned_data["date"]
        flow = self.cleaned_data["flow"]
        account = self.cleaned_data["account"]
        asset = self.instance.asset
        # check that there is not already a transaction or
        # trade on this exact date and account
        if Transaction.objects.filter(
            Q(date=date), Q(from_account=account) | Q(to_account=account)
        ).exists():
            raise forms.ValidationError(
                "There is already a transaction at this date and account."
            )
        if Trade.objects.filter(date=date, account=account).exists():
            raise forms.ValidationError(
                "There is already a trade at this date and account."
            )
        # check that enough asset is available if asset is withdrawn
        # TODO exclude the own instance from the available calculation
        if flow < 0 and account.get_amount_asset_before_date(asset, date) < abs(flow):
            raise forms.ValidationError(
                "There is not enough asset on this account to support this flow."
            )


###
# CryptoPriceFetcher
###
class PriceFetcherForm(forms.ModelForm):
    class Meta:
        model = PriceFetcher
        fields = ["asset", "fetcher_type", "data"]

    def __init__(self, depot, *args, **kwargs):
        super(PriceFetcherForm, self).__init__(*args, **kwargs)
        self.fields["asset"].queryset = depot.assets.all()

    def _create_human_error(self, error: forms.ValidationError) -> str:
        error_string = ""
        for e in error.errors():
            error_string += f"{e['loc'][0]}: {e['msg']}\n"
        return error_string

    def clean_data(self):
        data = self.cleaned_data["data"]
        if self.cleaned_data["fetcher_type"] == "COINGECKO":
            try:
                CoinGeckoFetcherInput(**data)
            except forms.ValidationError as e:
                raise forms.ValidationError(self._create_human_error(e))
        elif self.cleaned_data["fetcher_type"] in ["WEBSITE", "SELENIUM"]:
            try:
                WebsiteFetcherInput(**data)
            except forms.ValidationError as e:
                raise forms.ValidationError(self._create_human_error(e))
        else:
            self.add_error("fetcher_type", "This type is not supported.")
        return data

    def clean_fetcher_type(self):
        type = self.cleaned_data["fetcher_type"]
        if type not in map(lambda x: x[0], PriceFetcher.PRICE_FETCHER_TYPES):
            raise forms.ValidationError("This type is not supported.")
        return type


# price
class PriceEditForm(forms.ModelForm):
    class Meta:
        model = Price
        fields = ("price",)
