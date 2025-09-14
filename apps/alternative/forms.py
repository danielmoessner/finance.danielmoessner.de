from django import forms
from django.utils import timezone

from apps.alternative.models import Alternative, Depot, Flow, Value


class SubmitForm(forms.Form):
    pass


# depot
class DepotForm(forms.ModelForm):
    class Meta:
        model = Depot
        fields = ("name",)

    def __init__(self, user, *args, **kwargs):
        super(DepotForm, self).__init__(*args, **kwargs)
        self.instance.user = user


class DepotSelectForm(forms.Form):
    depot = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = ("depot",)

    def __init__(self, user, *args, **kwargs):
        super(DepotSelectForm, self).__init__(*args, **kwargs)
        self.fields["depot"].queryset = user.alternative_depots.all()


class DepotActiveForm(forms.ModelForm):
    class Meta:
        model = Depot
        fields = ("is_active",)


# alternative
class AlternativeForm(forms.ModelForm):
    class Meta:
        model = Alternative
        fields = (
            "name",
            "bucket",
            "is_archived",
        )

    def __init__(self, depot: Depot, *args, **kwargs):
        super(AlternativeForm, self).__init__(*args, **kwargs)
        self.instance.depot = depot
        self.fields["bucket"].queryset = depot.user.buckets.all()


class AlternativeSelectForm(forms.Form):
    alternative = forms.ModelChoiceField(widget=forms.Select, queryset=None)

    class Meta:
        fields = ("alternative",)

    def __init__(self, depot, *args, **kwargs):
        super(AlternativeSelectForm, self).__init__(*args, **kwargs)
        self.fields["alternative"].queryset = depot.alternatives.all()


# value
class ValueForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
        label="Date",
    )

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

    def clean(self):
        # get the cleaned data
        # alternative = self.cleaned_data["alternative"]
        # date = self.cleaned_data["date"]

        # # check that no flow or value already exists on this date
        # if Value.objects.filter(
        #     alternative=alternative, date=date
        # ).exists() or Flow.objects.filter(alternative=alternative, date=date):
        #     raise forms.ValidationError(
        #         "A flow or a value already exists on "
        #         "this date. Choose a different date."
        #     )

        # # a value before a flow occurs makes no sense
        # if not Flow.objects.filter(alternative=alternative, date__lt=date).exists():
        #     message = "There needs to be at least one flow before a value."
        #     raise forms.ValidationError(message)

        # # don't allow adding values if the value is 0
        # if Value.objects.filter(alternative=alternative, value__lte=0).exists():
        #     err = (
        #         "You can't add more values to this "
        #         "alternative, because its value is 0."
        #     )
        #     raise forms.ValidationError(err)

        # # check that, if the previous value or flow is
        # # a flow, the date is close to the flow
        # flow_qs = Flow.objects.filter(alternative=alternative)
        # value_qs = Value.objects.filter(alternative=alternative).exclude(
        #     pk=self.instance.pk
        # )
        # previous_value_or_flow = utils.get_closest_object_in_two_querysets(
        #     flow_qs, value_qs, date, direction="previous"
        # )
        # if (
        #     previous_value_or_flow
        #     and type(previous_value_or_flow) == Flow
        #     and previous_value_or_flow.date.day != date.day
        # ):
        #     message = (
        #         "Right before this value is a flow. The date"
        #         " of this value needs to be on the same day."
        #     )
        #     raise forms.ValidationError(message)

        # # return the cleaned data
        return self.cleaned_data


# flow
class FlowForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
        label="Date",
    )

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

    def clean(self):
        # date = self.cleaned_data["date"]
        # alternative = self.cleaned_data["alternative"]

        # # check that no flow or value already exists on this date
        # if Value.objects.filter(
        #     alternative=alternative, date=date
        # ).exists() or Flow.objects.filter(alternative=alternative, date=date):
        #     raise forms.ValidationError(
        #         "A flow or a value already exists on"
        #         " this date. Choose a different date."
        #     )

        # # don't allow adding flows if the value is 0
        # if Value.objects.filter(alternative=alternative, value__lte=0).exists():
        #     err = (
        #         "You can't add more flows to this alternative, because its value is 0."
        #     )
        #     raise forms.ValidationError(err)

        # # check that there is no other flow already
        # flow_qs = Flow.objects.filter(alternative=alternative).exclude(
        #     pk=self.instance.pk
        # )
        # value_qs = Value.objects.filter(alternative=alternative)
        # # check that there is no flow right before this flow
        # previous_value_or_flow = utils.get_closest_object_in_two_querysets(
        #     flow_qs, value_qs, date, direction="previous"
        # )
        # if previous_value_or_flow and type(previous_value_or_flow) == Flow:
        #     message = (
        #         "A flow can not be followed by a flow. "
        #         "There is a flow right before this flow."
        #     )
        #     raise forms.ValidationError(message)
        # # check that there is no flow right after this flow
        # next_value_or_flow = utils.get_closest_object_in_two_querysets(
        #     flow_qs, value_qs, date, direction="next"
        # )
        # if next_value_or_flow and type(next_value_or_flow) == Flow:
        #     message = (
        #         "A flow can not be followed by a flow."
        #         " There is a flow right after this flow."
        #     )
        #     raise forms.ValidationError(message)

        # # check that if a next value exists the date of the
        # # value is close to the date of the flow
        # next_values = (
        #     Value.objects.filter(alternative=alternative, date__gt=date)
        #     .exclude(pk=self.instance.pk)
        #     .order_by("date")
        # )
        # if next_values.exists() and next_values.first().date.day != date.day:
        #     message = (
        #         "The day from the date of the next value needs "
        #         "to be the same as the day from the date of this "
        #         "flow."
        #     )
        #     raise forms.ValidationError(message)

        # return the cleaned data
        return self.cleaned_data
