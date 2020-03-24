from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormMixin
from django.views import generic
from django.urls import reverse_lazy

from apps.banking.models import Category
from apps.banking.models import Account
from apps.banking.models import Change
from apps.banking.models import Depot
from apps.banking.forms import CategorySelectForm
from apps.banking.forms import AccountSelectForm
from apps.banking.forms import DepotActiveForm
from apps.banking.forms import DepotSelectForm
from apps.banking.forms import CategoryForm
from apps.banking.forms import AccountForm
from apps.banking.forms import ChangeForm
from apps.banking.forms import DepotForm
from apps.core.views import CustomAjaxDeleteMixin
from apps.core.views import CustomAjaxFormMixin
from django.http import HttpResponse

import json


# mixins
class CustomGetFormMixin(FormMixin):
    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        depot = self.request.user.banking_depots.get(is_active=True)
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


class SetActiveDepotView(LoginRequiredMixin, CustomGetFormUserMixin, generic.UpdateView):
    model = Depot
    form_class = DepotActiveForm
    template_name = "modules/form_snippet.njk"
    success_url = reverse_lazy("users:settings")


# account
class AddAccountView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    form_class = AccountForm
    model = Account
    template_name = "modules/form_snippet.njk"


class EditAccountView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Account
    form_class = AccountForm
    template_name = "modules/form_snippet.njk"


class DeleteAccountView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.FormView):
    model = Account
    template_name = "modules/form_snippet.njk"
    form_class = AccountSelectForm

    def form_valid(self, form):
        account = form.cleaned_data["account"]
        account.delete()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


# category
class AddCategoryView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    form_class = CategoryForm
    model = Category
    template_name = "modules/form_snippet.njk"


class EditCategoryView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "modules/form_snippet.njk"


class DeleteCategoryView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.FormView):
    model = Category
    template_name = "modules/form_snippet.njk"
    form_class = CategorySelectForm

    def form_valid(self, form):
        category = form.cleaned_data["category"]
        category.delete()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


# change
class AddChangeIndexView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    model = Change
    form_class = ChangeForm
    template_name = "modules/form_snippet.njk"


class AddChangeAccountView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    model = Change
    form_class = ChangeForm
    template_name = "modules/form_snippet.njk"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        account = Account.objects.get(slug=self.kwargs["slug"])
        kwargs.update({"initial": {"account": account}})
        return kwargs


class EditChangeView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Change
    form_class = ChangeForm
    template_name = "modules/form_snippet.njk"


class DeleteChangeView(LoginRequiredMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Change
    template_name = "modules/delete_snippet.njk"
