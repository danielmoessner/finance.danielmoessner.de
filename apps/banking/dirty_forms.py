from datetime import datetime
from typing import TypeVar

from django import forms
from django.db import transaction

from apps.banking.forms import ChangeField
from apps.banking.models import Account, Category, Change, Depot
from apps.crypto.models import Account as CryptoAccount
from apps.stocks.models import Bank as StocksAccount

A = TypeVar("A", Account, StocksAccount, CryptoAccount)


class MoveMoneyForm(forms.Form):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
        label="Date",
    )
    from_account = forms.ModelChoiceField(widget=forms.Select, queryset=None)
    to_account = forms.ChoiceField(widget=forms.Select)
    change = ChangeField()

    def __init__(self, depot: Depot, *args, **kwargs):
        super(MoveMoneyForm, self).__init__(*args, **kwargs)
        self.accounts = depot.user.get_active_accounts()
        self.fields["from_account"].queryset = depot.accounts.all()
        self.fields["to_account"].choices = self.get_choices_for_account()
        self.fields["date"].initial = datetime.now()
        if depot.most_money_moved_away:
            self.fields["from_account"].initial = depot.most_money_moved_away.pk
        print(depot.most_money_moved_away)
        print(depot.most_money_moved_to)
        if depot.most_money_moved_to:
            self.fields["to_account"].initial = self._get_acc_key(
                depot.most_money_moved_to
            )

    def get_choices_for_account(self):
        return [
            (None, "---------"),
            *[(self._get_acc_key(a), self._get_acc_name(a)) for a in self.accounts],
        ]

    def _get_acc_name(self, account: A):
        return f"{account.TYPE}: {account.name}"

    def _get_acc_key(self, account: A):
        return f"{account.__class__.__name__}-{account.pk}"

    def _clean_account(self, val) -> A:
        for a in self.accounts:
            if self._get_acc_key(a) == val:
                return a
        raise forms.ValidationError("Invalid account.")

    def clean_to_account(self):
        return self._clean_account(self.cleaned_data["to_account"])

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
        if isinstance(to_account, Account):
            category, _ = Category.objects.get_or_create(name="Money Movement")
        else:
            category, _ = Category.objects.get_or_create(name="Investments")
        with transaction.atomic():
            Change.objects.create(
                account=from_account,
                date=date,
                change=-change,
                description=description,
                category=category,
            )
            to_account.transfer_value(change, date, description)
        return True
