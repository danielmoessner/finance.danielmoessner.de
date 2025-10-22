import json
from typing import Callable

from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from apps.banking.dirty_forms import MoveMoneyForm
from apps.banking.forms import (
    AccountForm,
    AccountSelectForm,
    CategoryForm,
    CategorySelectForm,
    ChangeForm,
    ComdirectCompleteLoginForm,
    ComdirectImportChangesForm,
    ComdirectStartLoginForm,
    DeleteComdirectChange,
    DepotActiveForm,
    DepotForm,
    DepotSelectForm,
    ImportComdirectChange,
    ImportForm,
)
from apps.banking.models import (
    Account,
    Category,
    Change,
    ComdirectImport,
    ComdirectImportChange,
    Depot,
)
from apps.core.mixins import (
    AjaxResponseMixin,
    CustomAjaxDeleteMixin,
    CustomGetFormUserMixin,
    GetFormWithDepotAndInitialDataMixin,
    GetFormWithDepotMixin,
)
from apps.users.mixins import GetUserMixin
from apps.users.models import StandardUser


class GetDepotMixin:
    get_user: Callable[[], StandardUser]

    def get_depot(self):
        return self.get_user().banking_depots.get(is_active=True)


class CustomGetFormMixin:
    get_form_class: Callable[[], type]
    get_form_kwargs: Callable[[], dict]
    get_user: Callable[[], StandardUser]

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        depot = self.get_user().banking_depots.get(is_active=True)
        return form_class(depot, **self.get_form_kwargs())


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
        self.get_user().banking_depots.update(is_active=False)
        depot = self.get_object()
        form = DepotActiveForm(data={"is_active": True}, instance=depot)
        if form.is_valid():
            form.save()
        url = "{}?tab=banking".format(
            reverse_lazy("users:settings", args=[self.get_user().pk])
        )
        return HttpResponseRedirect(url)


class AddAccountView(
    GetUserMixin, CustomGetFormMixin, AjaxResponseMixin, generic.CreateView
):
    form_class = AccountForm
    model = Account
    template_name = "symbols/form_snippet.j2"


class EditAccountView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotMixin,
    AjaxResponseMixin,
    generic.UpdateView,
):
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


class AddCategoryView(
    GetUserMixin, CustomGetFormMixin, AjaxResponseMixin, generic.CreateView
):
    form_class = CategoryForm
    model = Category
    template_name = "symbols/form_snippet.j2"


class EditCategoryView(
    GetUserMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView
):
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


class AddChangeView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotAndInitialDataMixin,
    AjaxResponseMixin,
    generic.CreateView,
):
    model = Change
    form_class = ChangeForm
    template_name = "symbols/form_snippet.j2"


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


class MoneyMoveView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotAndInitialDataMixin,
    AjaxResponseMixin,
    generic.FormView,
):
    template_name = "symbols/form_snippet.j2"
    form_class = MoveMoneyForm


class ImportView(
    GetUserMixin,
    GetDepotMixin,
    GetFormWithDepotAndInitialDataMixin,
    AjaxResponseMixin,
    generic.FormView,
):
    template_name = "symbols/form_snippet.j2"
    form_class = ImportForm


class ComdirectImportView(
    GetUserMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView
):
    model = ComdirectImport
    template_name = "symbols/form_snippet.j2"

    def get_form_class(self):
        if self.request.session.get("comdirect_import_step") == "login_completed":
            return ComdirectImportChangesForm
        if self.request.session.get("comdirect_import_step") == "login_started":
            return ComdirectCompleteLoginForm
        if self.request.session.get("comdirect_import_step") == "import_completed":
            return ComdirectImportChangesForm
        return ComdirectStartLoginForm

    def get_form(self, form_class=None):
        form_class = self.get_form_class()
        depot = self.get_user().banking_depots.get(is_active=True)
        session = self.request.session
        return form_class(depot, session, **self.get_form_kwargs())

    def get_queryset(self):
        return ComdirectImport.objects.filter(
            account__in=Account.objects.filter(
                depot__in=self.get_user().banking_depots.all()
            )
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        if response.status_code != 200:
            self.request.session["comdirect_import_step"] = ""
            return response

        if self.request.session.get("comdirect_import_step") == "import_completed":
            return response

        form_class = self.get_form_class()
        return self.form_invalid(
            form=self.get_form(form_class)
        )  # to get to the next step but kinda hacky to use form invalid response for it


class ComdirectImportChangeView(
    GetUserMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView
):
    model = ComdirectImportChange
    form_class = ImportComdirectChange
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return ComdirectImportChange.objects.filter(
            comdirect_import__account__in=Account.objects.filter(
                depot__in=self.get_user().banking_depots.all()
            )
        )


class DeleteComdirectChangeView(
    GetUserMixin, CustomGetFormMixin, AjaxResponseMixin, generic.UpdateView
):
    model = ComdirectImportChange
    form_class = DeleteComdirectChange
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return ComdirectImportChange.objects.filter(
            comdirect_import__account__in=Account.objects.filter(
                depot__in=self.get_user().banking_depots.all()
            )
        )
