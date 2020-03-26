from django.contrib.auth.forms import UserCreationForm
from django import forms

from .models import StandardUser


class CreateStandardUserForm(UserCreationForm):
    class Meta:
        model = StandardUser
        fields = (
            "username",
            "password1",
            "password2",
        )


class SignInUserForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)

    class Meta:
        fields = (
            "username",
            "password"
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
            "date_format",
            "front_page"
        )


class UpdateCryptoStandardUserForm(forms.ModelForm):
    class Meta:
        model = StandardUser
        fields = (
            "rounded_numbers",
        )
