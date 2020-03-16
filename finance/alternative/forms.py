from django.utils import timezone
from django import forms

from finance.alternative.models import Alternative
from finance.alternative.models import Timespan
from finance.alternative.models import Value
from finance.alternative.models import Depot
from finance.alternative.models import Flow
from finance.core.utils import create_slug

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

        # a value before a flow occurs makes no sense
        if not Flow.objects.filter(alternative=alternative).exists():
            err = 'Add a flow before you add a value.'
            raise forms.ValidationError(err)

        # don't allow adding values if the value is 0
        if Value.objects.filter(alternative=alternative, value__lte=0).exists():
            err = "You can't add more flows or values to this alternative, because its value is 0."
            raise forms.ValidationError(err)

        # date
        date = self.cleaned_data['date']
        if date <= Value.objects.filter(alternative=alternative).earliest('date').date:
            err = 'The date must be greater than the date of the first value.'
            raise forms.ValidationError(err)


# flow
class FlowForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.DateTimeInput(
        attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        input_formats=['%Y-%m-%dT%H:%M'], label='Date')
    value = forms.DecimalField(decimal_places=2, max_digits=15)

    class Meta:
        model = Flow
        fields = (
            'alternative',
            'date',
            'flow',
            'value',
        )
        help_texts = {
            'value': 'The value of this alternative after the flow.'
        }

    def __init__(self, depot, *args, **kwargs):
        super(FlowForm, self).__init__(*args, **kwargs)
        self.fields['alternative'].queryset = depot.alternatives.all()
        self.fields['date'].initial = timezone.now().date
        self.fields['value'].widget.attrs['min'] = 0

    def clean(self):
        # get the cleaned data
        alternative = self.cleaned_data['alternative']
        date = self.cleaned_data['date']

        # don't allow another flow at the same time
        critical_date = date - timedelta(seconds=1)
        if Flow.objects.filter(alternative=alternative, date=critical_date).exists() or \
                Flow.objects.filter(alternative=alternative, date=date).exists():
            err = "There already exists a Flow with that date and value."
            raise forms.ValidationError(err)

        # don't allow adding flows or values to alternatives that have no value
        if Value.objects.filter(alternative=alternative, value__lte=0).exists():
            err = "You can't add more flows to this alternative, because its value is 0."
            raise forms.ValidationError(err)

        # return
        return self.cleaned_data

    def save(self, commit=True):
        flow = super(FlowForm, self).save(commit=commit)
        if commit and flow.pk:
            date = flow.date + timedelta(seconds=1)
            Value.objects.create(alternative=flow.alternative, date=date, value=flow.flow)
        return flow


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
