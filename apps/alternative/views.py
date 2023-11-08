import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
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
    TabContextMixin,
)
from apps.users.mixins import GetUserMixin
from apps.users.models import StandardUser


###
# Depot: Detail, Create, Update, Delete, UpdateSetActive
###
class DetailDepotView(LoginRequiredMixin, TabContextMixin, generic.DetailView):
    template_name = "alternative/index.j2"
    model = Depot

    def get_object(self, _=None) -> Depot | None:
        user: StandardUser = self.request.user  # type: ignore
        return user.get_active_alternative_depot()

    def get_context_data(self, **kwargs):
        context = super(DetailDepotView, self).get_context_data(**kwargs)
        context["alternatives"] = self.object.alternatives.order_by("name")
        context["stats"] = self.object.get_stats()
        return context


class CreateDepotView(
    LoginRequiredMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.CreateView
):
    form_class = DepotForm
    model = Depot
    template_name = "symbols/form_snippet.j2"


class UpdateDepotView(
    LoginRequiredMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Depot
    form_class = DepotForm
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return self.request.user.alternative_depots.all()


class DeleteDepotView(
    LoginRequiredMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.FormView
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


class SetActiveDepotView(LoginRequiredMixin, SingleObjectMixin, generic.View):
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        return self.request.user.alternative_depots.all()

    def get(self, request, *args, **kwargs):
        depot = self.get_object()
        form = DepotActiveForm(data={"is_active": True}, instance=depot)
        if form.is_valid():
            form.save()
        url = "{}?tab=alternative".format(
            reverse_lazy("users:settings", args=[self.request.user.pk])
        )
        return HttpResponseRedirect(url)


class ResetDepotView(GetUserMixin, generic.View):
    def post(self, request, pk, *args, **kwargs):
        depot = self.get_user().alternative_depots.get(pk=pk)
        depot.reset_all()
        return HttpResponseRedirect(reverse_lazy("alternative:index"))


###
# Alternative: Detail, Create, Update, Delete
###
class DetailAlternativeView(LoginRequiredMixin, TabContextMixin, generic.DetailView):
    template_name = "alternative/alternative.j2"
    model = Alternative

    def get_queryset(self):
        return Alternative.objects.filter(
            depot__in=self.request.user.alternative_depots.all()
        )

    def get_context_data(self, **kwargs):
        context = super(DetailAlternativeView, self).get_context_data(**kwargs)
        context["depot"] = self.object.depot
        context["alternatives"] = (
            context["depot"].alternatives.order_by("name").select_related("depot")
        )
        context["flows_and_values"] = self.object.get_flows_and_values()
        context["stats"] = self.object.get_stats()
        return context


class CreateAlternativeView(
    LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.CreateView
):
    form_class = AlternativeForm
    model = Alternative
    template_name = "symbols/form_snippet.j2"


class UpdateAlternativeView(
    LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Alternative
    form_class = AlternativeForm
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return Alternative.objects.filter(
            depot__in=self.request.user.alternative_depots.all()
        )


class DeleteAlternativeView(
    LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.FormView
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


###
# Flow: Create, Update, Delete
###
class CreateFlowView(LoginRequiredMixin, AjaxResponseMixin, generic.CreateView):
    model = Flow
    form_class = FlowForm
    template_name = "symbols/form_snippet.j2"

    def get_form(self, form_class=None):
        depot = self.request.user.alternative_depots.get(is_active=True)
        if form_class is None:
            form_class = self.get_form_class()
        if self.request.method == "GET":
            return form_class(
                depot, initial=self.request.GET, **self.get_form_kwargs().pop("initial")
            )
        return form_class(depot, **self.get_form_kwargs())


class UpdateFlowView(
    LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Flow
    form_class = FlowForm
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return Flow.objects.filter(
            alternative__in=Alternative.objects.filter(
                depot__in=self.request.user.alternative_depots.all()
            )
        )


class DeleteFlowView(LoginRequiredMixin, CustomAjaxDeleteMixin, generic.DeleteView):
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


###
# Value: Create, Update, Delete
###
class CreateValueView(LoginRequiredMixin, AjaxResponseMixin, generic.CreateView):
    model = Value
    form_class = ValueForm
    template_name = "symbols/form_snippet.j2"

    def get_form(self, form_class=None):
        depot = self.request.user.alternative_depots.get(is_active=True)
        if form_class is None:
            form_class = self.get_form_class()
        if self.request.method == "GET":
            return form_class(
                depot, initial=self.request.GET, **self.get_form_kwargs().pop("initial")
            )
        return form_class(depot, **self.get_form_kwargs())


class UpdateValueView(
    LoginRequiredMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Value
    form_class = ValueForm
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return Value.objects.filter(
            alternative__in=Alternative.objects.filter(
                depot__in=self.request.user.alternative_depots.all()
            )
        )


class DeleteValueView(LoginRequiredMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Value
    template_name = "symbols/delete_snippet.j2"

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
