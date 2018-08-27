from django.views.generic.edit import FormMixin
from django.views import generic
from django.urls import reverse_lazy

from finance.alternative.models import Timespan
from finance.alternative.models import Alternative
from finance.alternative.models import Value
from finance.alternative.models import Flow
from finance.alternative.models import Depot
from finance.alternative.forms import TimespanActiveForm
from finance.alternative.forms import DepotActiveForm
from finance.alternative.forms import DepotSelectForm
from finance.alternative.forms import TimespanForm
from finance.alternative.forms import AlternativeForm
from finance.alternative.forms import AlternativeSelectForm
from finance.alternative.forms import FlowForm
from finance.alternative.forms import ValueForm
from finance.alternative.forms import DepotForm
from finance.core.views import CustomAjaxDeleteMixin
from finance.core.views import CustomAjaxFormMixin
from django.http import HttpResponse

import json


# mixins
class CustomGetFormMixin(FormMixin):
    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        depot = self.request.user.alternative_depots.get(is_active=True)
        return form_class(depot, **self.get_form_kwargs())


class CustomGetFormUserMixin(object):
    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        user = self.request.user
        return form_class(user, **self.get_form_kwargs())


# depot
class AddDepotView(CustomGetFormUserMixin, CustomAjaxFormMixin, generic.CreateView):
    form_class = DepotForm
    model = Depot
    template_name = "modules/form_snippet.njk"


class EditDepotView(CustomGetFormUserMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Depot
    form_class = DepotForm
    template_name = "modules/form_snippet.njk"


class DeleteDepotView(CustomGetFormUserMixin, CustomAjaxFormMixin, generic.FormView):
    model = Depot
    template_name = "modules/form_snippet.njk"
    form_class = DepotSelectForm

    def form_valid(self, form):
        depot = form.cleaned_data["depot"]
        user = depot.user
        depot.delete()
        if user.banking_depots.count() <= 0:
            user.banking_is_active = False
            user.save()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


class SetActiveDepotView(CustomGetFormUserMixin, generic.UpdateView):
    model = Depot
    form_class = DepotActiveForm
    template_name = "modules/form_snippet.njk"
    success_url = reverse_lazy("users:settings")


# alternative
class AddAlternativeView(CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    form_class = AlternativeForm
    model = Alternative
    template_name = "modules/form_snippet.njk"


class EditAlternativeView(CustomGetFormMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Alternative
    form_class = AlternativeForm
    template_name = "modules/form_snippet.njk"


class DeleteAlternativeView(CustomGetFormMixin, CustomAjaxFormMixin, generic.FormView):
    model = Alternative
    template_name = "modules/form_snippet.njk"
    form_class = AlternativeSelectForm

    def form_valid(self, form):
        alternative = form.cleaned_data["alternative"]
        alternative.delete()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


# value
class AddValueView(CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    model = Value
    form_class = ValueForm
    template_name = "modules/form_snippet.njk"


class AddValueAlternativeView(CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    model = Value
    form_class = ValueForm
    template_name = "modules/form_snippet.njk"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        alternative = Alternative.objects.get(slug=self.kwargs["slug"])
        kwargs.update({"initial": {"alternative": alternative}})
        return kwargs


class EditValueView(CustomGetFormMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Value
    form_class = ValueForm
    template_name = "modules/form_snippet.njk"


class DeleteValueView(CustomAjaxDeleteMixin, generic.DeleteView):
    model = Value
    template_name = "modules/delete_snippet.njk"


# flow
class AddFlowView(CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    model = Flow
    form_class = FlowForm
    template_name = "modules/form_snippet.njk"


class AddFlowAlternativeView(CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    model = Flow
    form_class = FlowForm
    template_name = "modules/form_snippet.njk"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        alternative = Alternative.objects.get(slug=self.kwargs["slug"])
        kwargs.update({"initial": {"alternative": alternative}})
        return kwargs


class EditFlowView(CustomGetFormMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Flow
    form_class = FlowForm
    template_name = "modules/form_snippet.njk"


class DeleteFlowView(CustomAjaxDeleteMixin, generic.DeleteView):
    model = Flow
    template_name = "modules/delete_snippet.njk"


# timespan
class AddTimespanView(CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    form_class = TimespanForm
    model = Timespan
    template_name = "modules/form_snippet.njk"


class SetActiveTimespanView(CustomGetFormMixin, generic.UpdateView):
    model = Timespan
    form_class = TimespanActiveForm
    template_name = "modules/form_snippet.njk"
    success_url = reverse_lazy("alternative:index")


class DeleteTimespanView(CustomGetFormMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Timespan
    template_name = "modules/delete_snippet.njk"
    form_class = TimespanForm
