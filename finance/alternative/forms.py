from django.utils import timezone
from django import forms

from finance.alternative.models import Alternative
from finance.alternative.models import Timespan
from finance.alternative.models import Value
from finance.alternative.models import Depot
from finance.alternative.models import Flow
from finance.core.utils import create_slug
import finance.alternative.utils as utils

from datetime import timedelta


# depot
class DepotForm(forms.ModelForm):
    class Meta:
        model = Depot
        fields = (
            'name',
        )

    def __init__(self, user, *args, **kwargs):
        super(DepotForm, self).__init__(*args, **kwargs)
        self.instance.user = user


class DepotSelectForm(forms.Form):
    depot = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = (
            'depot',
        )

    def __init__(self, user, *args, **kwargs):
        super(DepotSelectForm, self).__init__(*args, **kwargs)
        self.fields['depot'].queryset = user.alternative_depots.all()


class DepotActiveForm(forms.ModelForm):
    class Meta:
        model = Depot
        fields = ('is_active',)

    def __init__(self, user, *args, **kwargs):
        super(DepotActiveForm, self).__init__(*args, **kwargs)
        user.alternative_depots.update(is_active=False)


# alternative
class AlternativeForm(forms.ModelForm):
    class Meta:
        model = Alternative
        fields = (
            'name',
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
            'alternative',
        )

    def __init__(self, depot, *args, **kwargs):
        super(AlternativeSelectForm, self).__init__(*args, **kwargs)
        self.fields['alternative'].queryset = depot.alternatives.all()


# value
class ValueForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.DateTimeInput(
        attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        input_formats=['%Y-%m-%dT%H:%M'], label='Date')

    class Meta:
        model = Value
        fields = (
            'alternative',
            'date',
            'value',
        )

    def __init__(self, depot, *args, **kwargs):
        super(ValueForm, self).__init__(*args, **kwargs)
        self.fields['alternative'].queryset = depot.alternatives.all()
        self.fields['date'].initial = timezone.now()

    def clean(self):
        # get the cleaned data
        alternative = self.cleaned_data['alternative']
        date = self.cleaned_data['date']

        # a value before a flow occurs makes no sense
        if not Flow.objects.filter(alternative=alternative, date__lt=date).exists():
            message = 'There needs to be at least one flow before a value.'
            raise forms.ValidationError(message)

        # don't allow adding values if the value is 0
        if Value.objects.filter(alternative=alternative, value__lte=0).exists():
            err = "You can't add more values to this alternative, because its value is 0."
            raise forms.ValidationError(err)

        # check that if the previous value or flow is a flow that the date is close to the flow
        flow_qs = Flow.objects.filter(alternative=alternative)
        value_qs = Value.objects.filter(alternative=alternative).exclude(pk=self.instance.pk)
        previous_value_or_flow = utils.get_closest_value_or_flow(flow_qs, value_qs, date, direction='previous')
        if (
                previous_value_or_flow and type(previous_value_or_flow) == Flow and
                abs(previous_value_or_flow.date - date) > timedelta(days=2)
        ):
            message = "Right before this value is a flow. The date of the value needs to be closer than 2 days."
            raise forms.ValidationError(message)

        # return the cleaned data
        return self.cleaned_data


# flow
class FlowForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.DateTimeInput(
        attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        input_formats=['%Y-%m-%dT%H:%M'], label='Date')

    class Meta:
        model = Flow
        fields = (
            'alternative',
            'date',
            'flow',
        )

    def __init__(self, depot, *args, **kwargs):
        super(FlowForm, self).__init__(*args, **kwargs)
        self.fields['alternative'].queryset = depot.alternatives.all()
        self.fields['date'].initial = timezone.now().date

    def clean(self):
        date = self.cleaned_data['date']
        alternative = self.cleaned_data['alternative']

        # don't allow adding flows if the value is 0
        if Value.objects.filter(alternative=alternative, value__lte=0).exists():
            err = "You can't add more flows to this alternative, because its value is 0."
            raise forms.ValidationError(err)

        # check that there is no other flow already
        flow_qs = Flow.objects.filter(alternative=alternative).exclude(pk=self.instance.pk)
        value_qs = Value.objects.filter(alternative=alternative)
        # check that there is no flow right before this flow
        previous_value_or_flow = utils.get_closest_value_or_flow(flow_qs, value_qs, date, direction='previous')
        if previous_value_or_flow and type(previous_value_or_flow) == Flow:
            message = "A flow can not be followed by a flow. There is a flow right before this flow."
            raise forms.ValidationError(message)
        # check that there is no flow right after this flow
        next_value_or_flow = utils.get_closest_value_or_flow(flow_qs, value_qs, date, direction='previous')
        if next_value_or_flow and type(next_value_or_flow) == Flow:
            message = "A flow can not be followed by a flow. There is a flow right after this flow."
            raise forms.ValidationError(message)

        # return the cleaned data
        return self.cleaned_data


# timespan
class TimespanForm(forms.ModelForm):
    start_date = forms.DateTimeField(widget=forms.DateTimeInput(
        attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        input_formats=['%Y-%m-%dT%H:%M'], label='Start Date (not required)', required=False)
    end_date = forms.DateTimeField(widget=forms.DateTimeInput(
        attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        input_formats=['%Y-%m-%dT%H:%M'], label='End Date (not required)', required=False)

    class Meta:
        model = Timespan
        fields = (
            'name',
            'start_date',
            'end_date'
        )

    def __init__(self, depot, *args, **kwargs):
        super(TimespanForm, self).__init__(*args, **kwargs)
        self.instance.depot = depot


class TimespanActiveForm(forms.ModelForm):
    class Meta:
        model = Timespan
        fields = ('is_active',)

    def __init__(self, depot, *args, **kwargs):
        super(TimespanActiveForm, self).__init__(*args, **kwargs)
        depot.timespans.update(is_active=False)
