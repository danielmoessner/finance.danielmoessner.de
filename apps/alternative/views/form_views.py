from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormMixin
from django.shortcuts import get_object_or_404
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy

from apps.alternative.models import Timespan
from apps.alternative.models import Alternative
from apps.alternative.models import Value
from apps.alternative.models import Flow
from apps.alternative.models import Depot
from apps.alternative.forms import TimespanActiveForm
from apps.alternative.forms import DepotActiveForm
from apps.alternative.forms import DepotSelectForm
from apps.alternative.forms import TimespanForm
from apps.alternative.forms import AlternativeForm
from apps.alternative.forms import AlternativeSelectForm
from apps.alternative.forms import FlowForm
from apps.alternative.forms import ValueForm
from apps.alternative.forms import DepotForm
from apps.core.views import CustomAjaxDeleteMixin
from apps.core.views import CustomAjaxFormMixin

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
class AddDepotView(LoginRequiredMixin, CustomGetFormUserMixin, CustomAjaxFormMixin, generic.CreateView):
    form_class = DepotForm
    model = Depot
    template_name = "modules/form_snippet.njk"


class EditDepotView(LoginRequiredMixin, CustomGetFormUserMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Depot
    form_class = DepotForm
    template_name = "modules/form_snippet.njk"


class DeleteDepotView(LoginRequiredMixin, CustomGetFormUserMixin, CustomAjaxFormMixin, generic.FormView):
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


class SetActiveDepotView(LoginRequiredMixin, generic.View):
    http_method_names = ['get', 'head', 'options']

    def get(self, request, pk, *args, **kwargs):
        depot = get_object_or_404(self.request.user.alternative_depots.all(), pk=pk)
        form = DepotActiveForm(data={'is_active': True}, instance=depot)
        if form.is_valid():
            form.save()
        url = '{}?tab=alternative'.format(reverse_lazy('users:settings', args=[self.request.user.pk]))
        return HttpResponseRedirect(url)


# alternative
class AddAlternativeView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    form_class = AlternativeForm
    model = Alternative
    template_name = "modules/form_snippet.njk"


class EditAlternativeView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Alternative
    form_class = AlternativeForm
    template_name = "modules/form_snippet.njk"


class DeleteAlternativeView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.FormView):
    model = Alternative
    template_name = "modules/form_snippet.njk"
    form_class = AlternativeSelectForm

    def form_valid(self, form):
        alternative = form.cleaned_data["alternative"]
        alternative.delete()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


# value
class AddValueView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    model = Value
    form_class = ValueForm
    template_name = "modules/form_snippet.njk"


class AddValueAlternativeView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    model = Value
    form_class = ValueForm
    template_name = "modules/form_snippet.njk"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        alternative = Alternative.objects.get(slug=self.kwargs["slug"])
        kwargs.update({"initial": {"alternative": alternative}})
        return kwargs


class EditValueView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Value
    form_class = ValueForm
    template_name = "modules/form_snippet.njk"


class DeleteValueView(LoginRequiredMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Value
    template_name = "modules/delete_snippet.njk"


# flow
class AddFlowView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    model = Flow
    form_class = FlowForm
    template_name = "modules/form_snippet.njk"


class AddFlowAlternativeView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    model = Flow
    form_class = FlowForm
    template_name = "modules/form_snippet.njk"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        alternative = Alternative.objects.get(slug=self.kwargs["slug"])
        kwargs.update({"initial": {"alternative": alternative}})
        return kwargs


class EditFlowView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Flow
    form_class = FlowForm
    template_name = "modules/form_snippet.njk"


class DeleteFlowView(LoginRequiredMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Flow
    template_name = "modules/delete_snippet.njk"


# timespan
class AddTimespanView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    form_class = TimespanForm
    model = Timespan
    template_name = "modules/form_snippet.njk"


class SetActiveTimespanView(LoginRequiredMixin, CustomGetFormMixin, generic.UpdateView):
    model = Timespan
    form_class = TimespanActiveForm
    template_name = "modules/form_snippet.njk"
    success_url = reverse_lazy("alternative:index")


class DeleteTimespanView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Timespan
    template_name = "modules/delete_snippet.njk"
    form_class = TimespanForm
