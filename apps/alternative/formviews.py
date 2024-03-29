import json
from typing import Callable

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from apps.alternative.forms import (
    AlternativeForm,
    AlternativeSelectForm,
    DepotActiveForm,
    DepotForm,
    DepotSelectForm,
    FlowForm,
    ValueForm,
)
from apps.alternative.mixins import CustomGetFormMixin
from apps.alternative.models import Alternative, Depot, Flow, Value
from apps.core.mixins import (
    AjaxResponseMixin,
    CustomAjaxDeleteMixin,
    CustomGetFormUserMixin,
    GetFormWithDepotAndInitialDataMixin,
)
from apps.users.mixins import GetUserMixin
from apps.users.models import StandardUser


class GetDepotMixin:
    get_user: Callable[[], StandardUser]

    def get_depot(self):
        return self.get_user().alternative_depots.get(is_active=True)


class CreateDepotView(
    GetUserMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.CreateView
):
    form_class = DepotForm
    model = Depot
    template_name = "symbols/form_snippet.j2"


class UpdateDepotView(
    GetUserMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Depot
    form_class = DepotForm
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return self.get_user().alternative_depots.all()


class DeleteDepotView(
    GetUserMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.FormView
):
    model = Depot
    template_name = "symbols/form_snippet.j2"
    form_class = DepotSelectForm

    def form_valid(self, form):
        depot = form.cleaned_data["depot"]
        user = depot.user
        depot.delete()
        if user.banking_depots.count() <= 0:
            user.banking_is_active = False
            user.save()
        return HttpResponse(
            json.dumps({"valid": True}), content_type="application/json"
        )


class SetActiveDepotView(GetUserMixin, SingleObjectMixin, generic.View):
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        return self.get_user().alternative_depots.all()

    def get(self, request, *args, **kwargs):
        self.get_user().alternative_depots.update(is_active=False)
        depot = self.get_object()
        form = DepotActiveForm(data={"is_active": True}, instance=depot)
        if form.is_valid():
            form.save()
        url = "{}?tab=alternative".format(
            reverse_lazy("users:settings", args=[self.get_user().pk])
        )
        return HttpResponseRedirect(url)


class ResetDepotView(GetUserMixin, generic.View):
    def post(self, request, pk, *args, **kwargs):
        depot = self.get_user().alternative_depots.get(pk=pk)
        depot.reset_all()
        return HttpResponseRedirect(reverse_lazy("alternative:index"))


class CreateAlternativeView(
    GetUserMixin, CustomGetFormMixin, AjaxResponseMixin, generic.CreateView
):
    form_class = AlternativeForm
    model = Alternative
    template_name = "symbols/form_snippet.j2"


class UpdateAlternativeView(
    GetUserMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Alternative
    form_class = AlternativeForm
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return Alternative.objects.filter(
            depot__in=self.get_user().alternative_depots.all()
        )


class DeleteAlternativeView(
    GetUserMixin, CustomGetFormMixin, AjaxResponseMixin, generic.FormView
):
    model = Alternative
    template_name = "symbols/form_snippet.j2"
    form_class = AlternativeSelectForm

    def form_valid(self, form):
        alternative = form.cleaned_data["alternative"]
        alternative.delete()
        return HttpResponse(
            json.dumps({"valid": True}), content_type="application/json"
        )


class CreateFlowView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotAndInitialDataMixin,
    AjaxResponseMixin,
    generic.CreateView,
):
    model = Flow
    form_class = FlowForm
    template_name = "symbols/form_snippet.j2"
    object: Flow


class UpdateFlowView(
    GetUserMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Flow
    form_class = FlowForm
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return Flow.objects.filter(
            alternative__in=Alternative.objects.filter(
                depot__in=self.get_user().alternative_depots.all()
            )
        )


class DeleteFlowView(GetUserMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Flow
    template_name = "symbols/delete_snippet.j2"

    # def delete(self, request, *args, **kwargs):
    #     flow = self.get_object()

    # test that calculations are not being fucked up by deleting some random flow
    # if (
    #     Value.objects.filter(
    #         alternative=flow.alternative, date__gt=flow.date
    #     ).exists()
    #     or Flow.objects.filter(
    #         alternative=flow.alternative, date__gt=flow.date
    #     ).exists()
    # ):
    #     message = (
    #         "You can only delete this flow if there is no flow or value afterwards."
    #     )
    #     messages.error(request, message)
    # else:
    #     flow.delete()
    # return HttpResponse(
    #     json.dumps({"valid": True}), content_type="application/json"
    # )


class CreateValueView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotAndInitialDataMixin,
    AjaxResponseMixin,
    generic.CreateView,
):
    model = Value
    form_class = ValueForm
    template_name = "symbols/form_snippet.j2"

    def get_form(self, form_class=None):
        depot = self.get_user().alternative_depots.get(is_active=True)
        if form_class is None:
            form_class = self.get_form_class()
        if self.request.method == "GET":
            return form_class(
                depot, initial=self.request.GET, **self.get_form_kwargs().pop("initial")
            )
        return form_class(depot, **self.get_form_kwargs())


class UpdateValueView(
    GetUserMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Value
    form_class = ValueForm
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return Value.objects.filter(
            alternative__in=Alternative.objects.filter(
                depot__in=self.get_user().alternative_depots.all()
            )
        )


class DeleteValueView(GetUserMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Value
    template_name = "symbols/delete_snippet.j2"
    get_object: Callable[[], Value]

    def delete(self, request, *args, **kwargs):
        value = self.get_object()

        # test that calculations are not being fucked up by deleting some random value
        if (
            Value.objects.filter(
                alternative=value.alternative, date__gt=value.date
            ).exists()
            or Flow.objects.filter(
                alternative=value.alternative, date__gt=value.date
            ).exists()
        ):
            message = (
                "You can only delete this value if"
                " there is no flow or value afterwards."
            )
            messages.error(request, message)
        else:
            value.delete()
        return HttpResponse(
            json.dumps({"valid": True}), content_type="application/json"
        )
