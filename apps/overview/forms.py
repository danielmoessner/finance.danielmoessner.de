from django import forms
from .models import Bucket


class BucketForm(forms.ModelForm):
    class Meta:
        model = Bucket
        fields = ("name", )

    def __init__(self, user, *args, **kwargs):
        super(BucketForm, self).__init__(*args, **kwargs)
        self.instance.user = user
