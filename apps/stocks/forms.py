from django import forms
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


class AccountSelectForm(forms.Form):
    bank = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = (
            "bank",
        )

    def __init__(self, depot, *args, **kwargs):
        super(AccountSelectForm, self).__init__(*args, **kwargs)
        self.fields["bank"].queryset = depot.banks.all()
