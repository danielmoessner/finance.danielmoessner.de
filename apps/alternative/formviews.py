from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormMixin
from django.contrib import messages
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy

from apps.alternative.models import Alternative, Value, Flow, Depot
from apps.alternative.forms import DepotActiveForm, DepotSelectForm, AlternativeForm
from apps.alternative.forms import AlternativeSelectForm, FlowForm, ValueForm, DepotForm
from apps.core.views import AjaxResponseMixin, CustomGetFormUserMixin

import json


# mixins
class CustomGetFormMixin(FormMixin):
    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        depot = self.request.user.alternative_depots.get(is_active=True)
        return form_class(depot, **self.get_form_kwargs())


# depot
class AddDepotView(LoginRequiredMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.CreateView):
    form_class = DepotForm
    model = Depot
    template_name = "modules/form_snippet.njk"


class EditDepotView(LoginRequiredMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.UpdateView):
    model = Depot
    form_class = DepotForm
    template_name = "modules/form_snippet.njk"

    def get_queryset(self):
        return self.request.user.alternative_depots.all()


class DeleteDepotView(LoginRequiredMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.FormView):
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


class SetActiveDepotView(LoginRequiredMixin, SingleObjectMixin, generic.View):
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        return self.request.user.alternative_depots.all()

    def get(self, request, *args, **kwargs):
        depot = self.get_object()
        form = DepotActiveForm(data={'is_active': True}, instance=depot)
        if form.is_valid():
            form.save()
        url = '{}?tab=alternative'.format(reverse_lazy('users:settings', args=[self.request.user.pk]))
        return HttpResponseRedirect(url)


# alternative
class AddAlternativeView(LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.CreateView):
    form_class = AlternativeForm
    model = Alternative
    template_name = "modules/form_snippet.njk"


class EditAlternativeView(LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView):
    model = Alternative
    form_class = AlternativeForm
    template_name = "modules/form_snippet.njk"

    def get_queryset(self):
        return Alternative.objects.filter(depot__in=self.request.user.alternative_depots.all())


class DeleteAlternativeView(LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.FormView):
    model = Alternative
    template_name = "modules/form_snippet.njk"
    form_class = AlternativeSelectForm

    def form_valid(self, form):
        alternative = form.cleaned_data["alternative"]
        alternative.delete()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


# value
class AddValueView(LoginRequiredMixin, AjaxResponseMixin, generic.CreateView):
    model = Value
    form_class = ValueForm
    template_name = "modules/form_snippet.njk"

    def get_form(self, form_class=None):
        depot = self.request.user.alternative_depots.get(is_active=True)
        if form_class is None:
            form_class = self.get_form_class()
        if self.request.method == 'GET':
            return form_class(depot, initial=self.request.GET, **self.get_form_kwargs().pop('initial'))
        return form_class(depot, **self.get_form_kwargs())


class EditValueView(LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView):
    model = Value
    form_class = ValueForm
    template_name = "modules/form_snippet.njk"

    def get_queryset(self):
        return Value.objects.filter(
            alternative__in=Alternative.objects.filter(depot__in=self.request.user.alternative_depots.all()))


class DeleteValueView(LoginRequiredMixin, generic.DeleteView):
    model = Value
    template_name = "modules/delete_snippet.njk"

    def delete(self, request, *args, **kwargs):
        value = self.get_object()

        # test that calculations are not being fucked up by deleting some random value
        if (
                Value.objects.filter(alternative=value.alternative, date__gt=value.date).exists() or
                Flow.objects.filter(alternative=value.alternative, date__gt=value.date).exists()
        ):
            message = 'You can only delete this value if there is no flow or value afterwards.'
            messages.error(request, message)
        else:
            value.delete()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


# flow
class AddFlowView(LoginRequiredMixin, AjaxResponseMixin, generic.CreateView):
    model = Flow
    form_class = FlowForm
    template_name = "modules/form_snippet.njk"

    def get_form(self, form_class=None):
        depot = self.request.user.alternative_depots.get(is_active=True)
        if form_class is None:
            form_class = self.get_form_class()
        if self.request.method == 'GET':
            return form_class(depot, initial=self.request.GET, **self.get_form_kwargs().pop('initial'))
        return form_class(depot, **self.get_form_kwargs())


class EditFlowView(LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView):
    model = Flow
    form_class = FlowForm
    template_name = "modules/form_snippet.njk"

    def get_queryset(self):
        return Flow.objects.filter(
            alternative__in=Alternative.objects.filter(depot__in=self.request.user.alternative_depots.all()))


class DeleteFlowView(LoginRequiredMixin, generic.DeleteView):
    model = Flow
    template_name = "modules/delete_snippet.njk"

    def delete(self, request, *args, **kwargs):
        flow = self.get_object()

        # test that calculations are not being fucked up by deleting some random flow
        if (
                Value.objects.filter(alternative=flow.alternative, date__gt=flow.date).exists() or
                Flow.objects.filter(alternative=flow.alternative, date__gt=flow.date).exists()
        ):
            message = 'You can only delete this flow if there is no flow or value afterwards.'
            messages.error(request, message)
        else:
            flow.delete()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")
