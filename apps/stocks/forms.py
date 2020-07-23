from django import forms
from django.utils import timezone
from apps.stocks.models import Depot, Bank, Trade, Stock, Flow


###
# Depot
###
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
        fields = (
            "name",
        )

    def __init__(self, depot, *args, **kwargs):
        super(BankForm, self).__init__(*args, **kwargs)
        self.instance.depot = depot


class BankSelectForm(forms.Form):
    bank = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = (
            "bank",
        )

    def __init__(self, depot, *args, **kwargs):
        super(BankSelectForm, self).__init__(*args, **kwargs)
        self.fields["bank"].queryset = depot.banks.all()


###
# Stock
###
class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = (
            'name',
            "ticker",
        )

    def __init__(self, depot, *args, **kwargs):
        super(StockForm, self).__init__(*args, **kwargs)
        self.instance.depot = depot


class StockSelectForm(forms.Form):
    stock = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = (
            "stock",
        )

    def __init__(self, depot, *args, **kwargs):
        super(StockSelectForm, self).__init__(*args, **kwargs)
        self.fields["stock"].queryset = depot.stocks.all()


###
# Flow
###
class FlowForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.DateTimeInput(
        attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        input_formats=['%Y-%m-%dT%H:%M'], label='Date')

    class Meta:
        model = Flow
        fields = (
            'bank',
            'date',
            'flow',
        )

    def __init__(self, depot, *args, **kwargs):
        super(FlowForm, self).__init__(*args, **kwargs)
        self.fields['bank'].queryset = depot.banks.all()
        self.fields['date'].initial = timezone.now()

    def clean(self):
        cleaned_data = super().clean()
        date = self.cleaned_data['date']
        flow = self.cleaned_data['flow']
        bank = self.cleaned_data['bank']
        # check that there doesn't already exist a flow or trade on this particular date
        if bank.flows.filter(date=date).exists() or bank.trades.filter(date=date).exists():
            raise forms.ValidationError(
                'There exists already a flow or a trade on this particular date. Choose a different date.')
        # check that enough money is available if money is withdrawn
        if flow < 0:
            bank_balance = bank.get_balance_on_date(date)
            if (bank_balance + flow) < 0:
                msg = (
                    'There is not enough money on this bank to support this flow. '
                    'There are only {} € available.'.format(bank_balance)
                )
                raise forms.ValidationError(msg)
        # return
        return self.cleaned_data


###
# Trade
###
class TradeForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
                               input_formats=["%Y-%m-%dT%H:%M"], label="Date")

    class Meta:
        model = Trade
        fields = (
            "bank",
            "stock",
            "date",
            'buy_or_sell',
            "money_amount",
            "stock_amount",
        )

    def __init__(self, depot, *args, **kwargs):
        super(TradeForm, self).__init__(*args, **kwargs)
        self.fields["bank"].queryset = depot.banks.order_by("name")
        self.fields['stock'].queryset = depot.stocks.order_by('name')
        self.fields["date"].initial = timezone.now()

    def clean(self):
        cleaned_data = super().clean()
        bank = self.cleaned_data['bank']
        stock = self.cleaned_data['stock']
        buy_or_sell = self.cleaned_data['buy_or_sell']
        money_amount = self.cleaned_data['money_amount']
        stock_amount = self.cleaned_data['stock_amount']
        date = self.cleaned_data['date']
        if bank.flows.filter(date=date).exists() or bank.trades.filter(date=date).exists():
            raise forms.ValidationError(
                'There exists already a flow or a trade on this particular date. Choose a different date.')
        # check that buy and sell amount is positive because a trade doesnt make sense otherwise
        if money_amount < 0 or stock_amount < 0:
            raise forms.ValidationError('Sell and buy amount must be positive.')
        # check that enough money is available to buy the stocks
        if buy_or_sell == 'BUY':
            bank_balance = bank.get_balance_on_date(date)
            msg = (
                'There is not enough money on this bank to support this trade. '
                'This particular bank has {} € available.'.format(bank_balance)
            )
            if bank_balance < 0:
                raise forms.ValidationError(msg)
        # return
        return self.cleaned_data
