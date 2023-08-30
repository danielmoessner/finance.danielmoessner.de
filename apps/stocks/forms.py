from django import forms
from django.utils import timezone
from pydantic import ValidationError

from apps.core import utils
from apps.core.fetchers.website import WebsiteFetcherInput
from apps.stocks.fetchers.marketstack import MarketstackFetcherInput
from apps.stocks.models import (
    Bank,
    Depot,
    Dividend,
    Flow,
    Price,
    PriceFetcher,
    Stock,
    Trade,
)


###
# Depot
###
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
        self.fields["depot"].queryset = user.stock_depots.all()


class DepotActiveForm(forms.ModelForm):
    class Meta:
        model = Depot
        fields = ("is_active",)


###
# Bank
###
class BankForm(forms.ModelForm):
    class Meta:
        model = Bank
        fields = ("name",)

    def __init__(self, depot, *args, **kwargs):
        super(BankForm, self).__init__(*args, **kwargs)
        self.instance.depot = depot


class BankSelectForm(forms.Form):
    bank = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = ("bank",)

    def __init__(self, depot, *args, **kwargs):
        super(BankSelectForm, self).__init__(*args, **kwargs)
        self.fields["bank"].queryset = depot.banks.all()


###
# Stock
###
class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ("name", "ticker", "exchange")

    def __init__(self, depot, *args, **kwargs):
        super(StockForm, self).__init__(*args, **kwargs)
        self.instance.depot = depot


class EditStockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ("name", "ticker", "exchange")

    def __init__(self, depot, *args, **kwargs):
        super(EditStockForm, self).__init__(*args, **kwargs)
        self.instance.depot = depot


class StockSelectForm(forms.Form):
    stock = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = ("stock",)

    def __init__(self, depot, *args, **kwargs):
        super(StockSelectForm, self).__init__(*args, **kwargs)
        self.fields["stock"].queryset = depot.stocks.all()


###
# StockPriceFetcher
###
class PriceFetcherForm(forms.ModelForm):
    class Meta:
        model = PriceFetcher
        fields = ["stock", "fetcher_type", "data"]

    def __init__(self, depot, *args, **kwargs):
        super(PriceFetcherForm, self).__init__(*args, **kwargs)
        self.fields["stock"].queryset = depot.stocks.all()

    def _create_human_error(self, error: ValidationError) -> str:
        error_string = ""
        for e in error.errors():
            error_string += f"{e['loc'][0]}: {e['msg']}\n"
        return error_string

    def clean_data(self):
        data = self.cleaned_data["data"]
        if self.cleaned_data["fetcher_type"] == "MARKETSTACK":
            try:
                MarketstackFetcherInput(**data)
            except ValidationError as e:
                raise forms.ValidationError(self._create_human_error(e))
        elif self.cleaned_data["fetcher_type"] in ["WEBSITE", "SELENIUM"]:
            try:
                WebsiteFetcherInput(**data)
            except ValidationError as e:
                raise forms.ValidationError(self._create_human_error(e))
        else:
            self.add_error("fetcher_type", "This type is not supported.")
        return data

    def clean_fetcher_type(self):
        type = self.cleaned_data["fetcher_type"]
        if type not in map(lambda x: x[0], PriceFetcher.PRICE_FETCHER_TYPES):
            raise forms.ValidationError("This type is not supported.")
        return type


###
# Flow
###
class FlowForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
        label="Date",
        initial=timezone.now,
    )

    class Meta:
        model = Flow
        fields = ("bank", "date", "flow", "short_description")

    def __init__(self, depot, *args, **kwargs):
        super(FlowForm, self).__init__(*args, **kwargs)
        self.fields["bank"].queryset = depot.banks.all()
        if self.instance.pk:
            self.fields["bank"].disabled = True

    def clean(self):
        super().clean()
        date = self.cleaned_data["date"]
        flow = self.cleaned_data["flow"]
        bank = self.cleaned_data["bank"]

        # check that there doesn't already exist a flow or trade on this particular date
        instance_pk = self.instance.pk if self.instance.pk else 0
        if (
            bank.flows.filter(date=date).exclude(pk=instance_pk).exists()
            or bank.trades.filter(date=date).exists()
            or bank.dividends.filter(date=date).exists()
        ):
            raise forms.ValidationError(
                "There exists already a flow, trade or dividend "
                "on this particular date and time. "
                "Choose a different date."
            )
        if flow < 0:
            # check that enough money is available if money is withdrawn
            if self.instance:
                bank_balance = bank.get_balance_on_date(
                    date, exclude_flow=self.instance
                )
            else:
                bank_balance = bank.get_balance_on_date(date)
            if (bank_balance + flow) < 0:
                msg = (
                    "There is not enough money on this bank to support this flow. "
                    "There are only {} € available.".format(bank_balance)
                )
                raise forms.ValidationError(msg)
            # check that enough money is available after the money was withdrawn
            flow_or_trade = utils.get_closest_object_in_two_querysets(
                bank.flows.all(), bank.trades.all(), date, direction="next"
            )
            date = flow_or_trade.date if flow_or_trade else timezone.now()
            if self.instance:
                bank_balance = bank.get_balance_on_date(
                    date, exclude_trade=self.instance
                )
            else:
                bank_balance = bank.get_balance_on_date(date)
            if bank_balance + flow < 0:
                msg = (
                    "After this flow the balance would be {} on date {}."
                    " That is not possible. "
                    "You need to change the money amount.".format(
                        (bank_balance + flow), date.strftime("%d.%m.%Y")
                    )
                )
                raise forms.ValidationError(msg)
        # return
        return self.cleaned_data


###
# Dividend
###
class DividendForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
        label="Date",
        initial=timezone.now,
    )

    class Meta:
        model = Dividend
        fields = ("bank", "stock", "date", "dividend")

    def __init__(self, depot, *args, **kwargs):
        print(args, kwargs)
        super(DividendForm, self).__init__(*args, **kwargs)
        self.fields["bank"].queryset = depot.banks.order_by("name")
        self.fields["stock"].queryset = depot.stocks.order_by("name")
        if self.instance.pk:
            self.fields["bank"].disabled = True
            self.fields["stock"].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        date = self.cleaned_data["date"]
        bank = self.cleaned_data["bank"]
        stock = self.cleaned_data["stock"]
        # check that no flow, trade or dividend already existst on this date
        instance_pk = self.instance.pk if self.instance.pk else 0
        if (
            bank.flows.filter(date=date).exists()
            or bank.trades.filter(date=date).exists()
            or bank.dividends.filter(date=date).exclude(pk=instance_pk).exists()
            or stock.trades.filter(date=date).exists()
            or stock.dividends.filter(date=date).exclude(pk=instance_pk).exists()
        ):
            raise forms.ValidationError(
                "There exists already a flow, trade or "
                "dividend on this particular date and time. "
                "Choose a different date."
            )
        # return
        return cleaned_data

    def clean_dividend(self):
        dividend = self.cleaned_data["dividend"]
        if dividend <= 0:
            raise forms.ValidationError("The dividend needs to be greater than 0")
        return dividend


###
# Trade
###
class TradeForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
        label="Date",
        initial=timezone.now,
    )

    class Meta:
        model = Trade
        fields = (
            "bank",
            "stock",
            "date",
            "buy_or_sell",
            "money_amount",
            "stock_amount",
        )

    def __init__(self, depot, *args, **kwargs):
        super(TradeForm, self).__init__(*args, **kwargs)
        self.fields["bank"].queryset = depot.banks.order_by("name")
        self.fields["stock"].queryset = depot.stocks.order_by("name")
        if self.instance.pk:
            self.fields["bank"].disabled = True
            self.fields["stock"].disabled = True

    def clean(self):
        super().clean()
        bank = self.cleaned_data["bank"]
        stock = self.cleaned_data["stock"]
        buy_or_sell = self.cleaned_data["buy_or_sell"]
        money_amount = self.cleaned_data["money_amount"]
        stock_amount = self.cleaned_data["stock_amount"]
        date = self.cleaned_data["date"]
        # check that no flow or trade already exists on this date
        instance_pk = self.instance.pk if self.instance.pk else 0
        if (
            bank.flows.filter(date=date).exists()
            or bank.trades.filter(date=date).exclude(pk=instance_pk).exists()
            or bank.dividends.filter(date=date).exists()
            or stock.trades.filter(date=date).exclude(pk=instance_pk).exists()
            or stock.dividends.filter(date=date).exists()
        ):
            raise forms.ValidationError(
                "There exists already a flow, trade or"
                " dividend on this particular date and time. "
                "Choose a different date."
            )
        # check that buy and sell amount is positive because a
        # trade doesnt make sense otherwise
        if money_amount < 0 or stock_amount < 0:
            raise forms.ValidationError("Sell and buy amount must be positive.")
        # check that enough money is available to buy the stocks
        if buy_or_sell == "BUY":
            # check that enough money is available right on this date
            if self.instance:
                bank_balance = bank.get_balance_on_date(
                    date, exclude_trade=self.instance
                )
            else:
                bank_balance = bank.get_balance_on_date(date)
            if bank_balance - money_amount < 0:
                msg = (
                    "There is not enough money on this bank to support this trade. "
                    "This particular bank has {} € available.".format(bank_balance)
                )
                raise forms.ValidationError(msg)
            # check that the overall balance does not become
            # negative after this trade is added. this code checks the
            # balance after the next flow or trade and assures
            # that it is not negative. If no
            flow_or_trade = utils.get_closest_object_in_two_querysets(
                bank.flows.all(), bank.trades.all(), date, direction="next"
            )
            date = flow_or_trade.date if flow_or_trade else timezone.now()
            if self.instance:
                bank_balance = bank.get_balance_on_date(
                    date, exclude_trade=self.instance
                )
            else:
                bank_balance = bank.get_balance_on_date(date)
            if bank_balance - money_amount < 0:
                msg = (
                    "After this trade the balance would be {} on date {}."
                    " That is not possible. "
                    "You need to change the money amount.".format(
                        (bank_balance - money_amount), date.strftime("%d.%m.%Y")
                    )
                )
                raise forms.ValidationError(msg)
        # return
        return self.cleaned_data


###
# Price
###
class PriceForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S%z"],
        label="Date",
    )

    class Meta:
        model = Price
        fields = ("date", "ticker", "exchange", "price")

    def clean(self):
        cleaned_data = super().clean()
        if Price.objects.filter(
            ticker=cleaned_data["ticker"], date=cleaned_data["date"]
        ).exists():
            raise forms.ValidationError(
                "There exists already a price for this stock on this date."
            )
        return cleaned_data

    def clean_ticker(self):
        ticker = self.cleaned_data["ticker"]
        ticker = ticker.split(".")[0]
        return ticker


class PriceEditForm(forms.ModelForm):
    class Meta:
        model = Price
        fields = ("price",)
