from django.views.generic.edit import FormMixin
from django.views import generic
from django.urls import reverse_lazy

from finance.banking.models import Timespan
from finance.banking.models import Category
from finance.banking.models import Account
from finance.banking.models import Change
from finance.banking.models import Depot
from finance.banking.forms import CategorySelectForm
from finance.banking.forms import TimespanActiveForm
from finance.banking.forms import AccountSelectForm
from finance.banking.forms import DepotActiveForm
from finance.banking.forms import DepotSelectForm
from finance.banking.forms import TimespanForm
from finance.banking.forms import CategoryForm
from finance.banking.forms import AccountForm
from finance.banking.forms import ChangeForm
from finance.banking.forms import DepotForm
from finance.core.views import CustomAjaxDeleteMixin
from finance.core.views import CustomAjaxFormMixin
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
            user.update(banking_is_active=False)
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


class SetActiveDepotView(CustomGetFormUserMixin, generic.UpdateView):
    model = Depot
    form_class = DepotActiveForm
    template_name = "modules/form_snippet.njk"
    success_url = reverse_lazy("users:settings")


# account
class AddAccountView(CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    form_class = AccountForm
    model = Account
    template_name = "modules/form_snippet.njk"


class EditAccountView(CustomGetFormMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Account
    form_class = AccountForm
    template_name = "modules/form_snippet.njk"


class DeleteAccountView(CustomGetFormMixin, CustomAjaxFormMixin, generic.FormView):
    model = Account
    template_name = "modules/form_snippet.njk"
    form_class = AccountSelectForm

    def form_valid(self, form):
        account = form.cleaned_data["account"]
        account.delete()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


# category
class AddCategoryView(CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    form_class = CategoryForm
    model = Category
    template_name = "modules/form_snippet.njk"


class EditCategoryView(CustomGetFormMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "modules/form_snippet.njk"


class DeleteCategoryView(CustomGetFormMixin, CustomAjaxFormMixin, generic.FormView):
    model = Category
    template_name = "modules/form_snippet.njk"
    form_class = CategorySelectForm

    def form_valid(self, form):
        category = form.cleaned_data["category"]
        category.delete()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


# change
class AddChangeIndexView(CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    model = Change
    form_class = ChangeForm
    template_name = "modules/form_snippet.njk"


class AddChangeAccountView(CustomGetFormMixin, CustomAjaxFormMixin, generic.CreateView):
    model = Change
    form_class = ChangeForm
    template_name = "modules/form_snippet.njk"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        account = Account.objects.get(slug=self.kwargs["slug"])
        kwargs.update({"initial": {"account": account}})
        return kwargs


class EditChangeView(CustomGetFormMixin, CustomAjaxFormMixin, generic.UpdateView):
    model = Change
    form_class = ChangeForm
    template_name = "modules/form_snippet.njk"


class DeleteChangeView(CustomAjaxDeleteMixin, generic.DeleteView):
    model = Change
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
    success_url = reverse_lazy("banking:index")


class DeleteTimespanView(CustomGetFormMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Timespan
    template_name = "modules/delete_snippet.njk"
    form_class = TimespanForm
