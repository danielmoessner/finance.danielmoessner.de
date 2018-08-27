from django.utils import timezone
from django import forms

from finance.alternative.models import Alternative
from finance.alternative.models import Timespan
from finance.alternative.models import Value
from finance.alternative.models import Depot
from finance.alternative.models import Flow
from finance.core.utils import create_slug


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
        self.fields["depot"].queryset = user.alternative_depots.all()


class DepotActiveForm(forms.ModelForm):
    class Meta:
        model = Depot
        fields = ("is_active",)

    def __init__(self, user, *args, **kwargs):
        super(DepotActiveForm, self).__init__(*args, **kwargs)
        user.alternative_depots.update(is_active=False)


# alternative
class AlternativeForm(forms.ModelForm):
    class Meta:
        model = Alternative
        fields = (
            "name",
        )

    def __init__(self, depot, *args, **kwargs):
        super(AlternativeForm, self).__init__(*args, **kwargs)
        self.instance.depot = depot

    def save(self, commit=True):
        self.instance.slug = create_slug(self.instance, self.instance.name)
        return super(AlternativeForm, self).save(commit=commit)


class AlternativeSelectForm(forms.Form):
    alternative = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = (
            "alternative",
        )

    def __init__(self, depot, *args, **kwargs):
        super(AlternativeSelectForm, self).__init__(*args, **kwargs)
        self.fields["alternative"].queryset = depot.alternatives.all()


# value
class ValueForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"},
                                                          format="%Y-%m-%dT%H:%M"),
                               input_formats=["%Y-%m-%dT%H:%M"], label="Date")

    class Meta:
        model = Value
        fields = (
            "alternative",
            "date",
            "value",
        )

    def __init__(self, depot, *args, **kwargs):
        super(ValueForm, self).__init__(*args, **kwargs)
        self.fields["alternative"].queryset = depot.alternatives.all()
        self.fields["date"].initial = timezone.now()


# change
class FlowForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"},
                                                          format="%Y-%m-%dT%H:%M"),
                               input_formats=["%Y-%m-%dT%H:%M"], label="Date")

    class Meta:
        model = Flow
        fields = (
            "alternative",
            "date",
            "flow",
        )

    def __init__(self, depot, *args, **kwargs):
        super(FlowForm, self).__init__(*args, **kwargs)
        self.fields["alternative"].queryset = depot.alternatives.all()
        self.fields["date"].initial = timezone.now()


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
