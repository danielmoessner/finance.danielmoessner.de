from django.contrib.auth.forms import UserCreationForm
from django import forms

from .models import StandardUser


# standard user
class CreateStandardUserForm(UserCreationForm):
    class Meta:
        model = StandardUser
        fields = (
            "username",
            "password1",
            "password2",
        )


class UpdateStandardUserForm(forms.ModelForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = StandardUser
        fields = (
            "username",
            "email"
        )


class UpdateGeneralStandardUserForm(forms.ModelForm):
    class Meta:
        model = StandardUser
        fields = (
            "currency",
            "date_format",
            "front_page"
        )
        help_texts = {
            "currency": "USD is not enabled yet."
        }

    def clean_currency(self):
        data = self.cleaned_data["currency"]
        if data == "$":
            raise forms.ValidationError("USD is not enabled yet.")
        return data


class UpdateCryptoStandardUserForm(forms.ModelForm):
    class Meta:
        model = StandardUser
        fields = (
            "rounded_numbers",
        )
