import json

from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormMixin

from apps.banking.forms import (
    AccountForm,
    AccountSelectForm,
    CategoryForm,
    CategorySelectForm,
    ChangeForm,
    DepotActiveForm,
    DepotForm,
    DepotSelectForm,
)
from apps.banking.models import Account, Category, Change, Depot
from apps.core.mixins import (
    AjaxResponseMixin,
    CustomAjaxDeleteMixin,
    CustomGetFormUserMixin,
)
from apps.users.mixins import GetUserMixin


# mixins
class CustomGetFormMixin(FormMixin):
    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        depot = self.get_user().banking_depots.get(is_active=True)
        return form_class(depot, **self.get_form_kwargs())


# depot
class AddDepotView(
    GetUserMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.CreateView
):
    form_class = DepotForm
    model = Depot
    template_name = "symbols/form_snippet.j2"


class EditDepotView(
    GetUserMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Depot
    form_class = DepotForm
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return self.get_user().banking_depots.all()


class DeleteDepotView(
    GetUserMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.FormView
):
    model = Depot
    template_name = "symbols/form_snippet.j2"
    form_class = DepotSelectForm

    def form_valid(self, form):
        depot = form.cleaned_data["depot"]
        depot.delete()
        return HttpResponse(
            json.dumps({"valid": True}), content_type="application/json"
        )


class SetActiveDepotView(GetUserMixin, SingleObjectMixin, generic.View):
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        return self.get_user().banking_depots.all()

    def get(self, request, *args, **kwargs):
        depot = self.get_object()
        form = DepotActiveForm(data={"is_active": True}, instance=depot)
        if form.is_valid():
            form.save()
        url = "{}?tab=banking".format(
            reverse_lazy("users:settings", args=[self.get_user().pk])
        )
        return HttpResponseRedirect(url)


# account
class AddAccountView(
    GetUserMixin, CustomGetFormMixin, AjaxResponseMixin, generic.CreateView
):
    form_class = AccountForm
    model = Account
    template_name = "symbols/form_snippet.j2"


class EditAccountView(CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView):
    model = Account
    form_class = AccountForm
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return Account.objects.filter(depot__in=self.get_user().banking_depots.all())


class DeleteAccountView(
    GetUserMixin, CustomGetFormMixin, AjaxResponseMixin, generic.FormView
):
    model = Account
    template_name = "symbols/form_snippet.j2"
    form_class = AccountSelectForm

    def form_valid(self, form):
        account = form.cleaned_data["account"]
        account.delete()
        return HttpResponse(
            json.dumps({"valid": True}), content_type="application/json"
        )


# category
class AddCategoryView(
    GetUserMixin, CustomGetFormMixin, AjaxResponseMixin, generic.CreateView
):
    form_class = CategoryForm
    model = Category
    template_name = "symbols/form_snippet.j2"


class EditCategoryView(CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return Category.objects.filter(depot__in=self.get_user().banking_depots.all())


class DeleteCategoryView(
    GetUserMixin, CustomGetFormMixin, AjaxResponseMixin, generic.FormView
):
    model = Category
    template_name = "symbols/form_snippet.j2"
    form_class = CategorySelectForm

    def form_valid(self, form):
        category = form.cleaned_data["category"]
        category.delete()
        return HttpResponse(
            json.dumps({"valid": True}), content_type="application/json"
        )


# change
class AddChangeView(GetUserMixin, AjaxResponseMixin, generic.CreateView):
    model = Change
    form_class = ChangeForm
    template_name = "symbols/form_snippet.j2"

    def get_form(self, form_class=None):
        depot = self.get_user().banking_depots.get(is_active=True)
        if form_class is None:
            form_class = self.get_form_class()
        if self.request.method == "GET":
            return form_class(
                depot, initial=self.request.GET, **self.get_form_kwargs().pop("initial")
            )
        return form_class(depot, **self.get_form_kwargs())


class EditChangeView(
    GetUserMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView
):
    model = Change
    form_class = ChangeForm
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return Change.objects.filter(
            account__in=Account.objects.filter(
                depot__in=self.get_user().banking_depots.all()
            )
        )


class DeleteChangeView(GetUserMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Change
    template_name = "symbols/delete_snippet.j2"
