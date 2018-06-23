from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms

from .models import StandardUser


# STANDARDUSER
class AddStandardUserForm(UserCreationForm):
    class Meta:
        model = StandardUser
        fields = (
            "username",
            "password1",
            "password2",
        )


class EditStandardUserForm(UserChangeForm):
    class Meta:
        model = StandardUser
        fields = (
            "username",
            "email",
            "password",
        )


class EditStandardUserSpecialsForm(forms.ModelForm):
    class Meta:
        model = StandardUser
        fields = (
            "currency",
            "date_format",
            "rounded_numbers",
            "front_page"
        )
