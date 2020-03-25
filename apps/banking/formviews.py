from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormMixin
from django.views import generic
from django.http import HttpResponseRedirect
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
from apps.core.views import CustomAjaxDeleteMixin, CustomGetFormUserMixin, CustomAjaxResponseMixin
from django.http import HttpResponse

import json


# mixins
class CustomGetFormMixin(FormMixin):
    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        depot = self.request.user.banking_depots.get(is_active=True)
        return form_class(depot, **self.get_form_kwargs())


# depot
class AddDepotView(LoginRequiredMixin, CustomGetFormUserMixin, CustomAjaxResponseMixin, generic.CreateView):
    form_class = DepotForm
    model = Depot
    template_name = "modules/form_snippet.njk"


class EditDepotView(CustomGetFormUserMixin, CustomAjaxResponseMixin, generic.UpdateView):
    model = Depot
    form_class = DepotForm
    template_name = "modules/form_snippet.njk"

    def get_queryset(self):
        return self.request.user.banking_depots.all()


class DeleteDepotView(LoginRequiredMixin, CustomGetFormUserMixin, CustomAjaxResponseMixin, generic.FormView):
    model = Depot
    template_name = "modules/form_snippet.njk"
    form_class = DepotSelectForm

    def form_valid(self, form):
        depot = form.cleaned_data["depot"]
        depot.delete()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


class SetActiveDepotView(LoginRequiredMixin, SingleObjectMixin, generic.View):
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        return self.request.user.banking_depots.all()

    def get(self, request, *args, **kwargs):
        depot = self.get_object()
        form = DepotActiveForm(data={'is_active': True}, instance=depot)
        if form.is_valid():
            form.save()
        url = '{}?tab=banking'.format(reverse_lazy('users:settings', args=[self.request.user.pk]))
        return HttpResponseRedirect(url)


# account
class AddAccountView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.CreateView):
    form_class = AccountForm
    model = Account
    template_name = "modules/form_snippet.njk"


class EditAccountView(CustomGetFormMixin, CustomAjaxResponseMixin, generic.UpdateView):
    model = Account
    form_class = AccountForm
    template_name = "modules/form_snippet.njk"

    def get_queryset(self):
        return Account.objects.filter(depot__in=self.request.user.banking_depots.all())


class DeleteAccountView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.FormView):
    model = Account
    template_name = "modules/form_snippet.njk"
    form_class = AccountSelectForm

    def form_valid(self, form):
        account = form.cleaned_data["account"]
        account.delete()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


# category
class AddCategoryView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.CreateView):
    form_class = CategoryForm
    model = Category
    template_name = "modules/form_snippet.njk"


class EditCategoryView(CustomGetFormMixin, CustomAjaxResponseMixin, generic.UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "modules/form_snippet.njk"

    def get_queryset(self):
        return Category.objects.filter(depot__in=self.request.user.banking_depots.all())


class DeleteCategoryView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.FormView):
    model = Category
    template_name = "modules/form_snippet.njk"
    form_class = CategorySelectForm

    def form_valid(self, form):
        category = form.cleaned_data["category"]
        category.delete()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


# change
class AddChangeView(LoginRequiredMixin, CustomAjaxResponseMixin, generic.CreateView):
    model = Change
    form_class = ChangeForm
    template_name = "modules/form_snippet.njk"

    def get_form(self, form_class=None):
        depot = self.request.user.banking_depots.get(is_active=True)
        if form_class is None:
            form_class = self.get_form_class()
        if self.request.method == 'GET':
            return form_class(depot, initial=self.request.GET, **self.get_form_kwargs().pop('initial'))
        return form_class(depot, **self.get_form_kwargs())


class EditChangeView(LoginRequiredMixin, CustomGetFormMixin, CustomAjaxResponseMixin, generic.UpdateView):
    model = Change
    form_class = ChangeForm
    template_name = "modules/form_snippet.njk"

    def get_queryset(self):
        return Change.objects.filter(
            account__in=Account.objects.filter(depot__in=self.request.user.banking_depots.all()))


class DeleteChangeView(LoginRequiredMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Change
    template_name = "modules/delete_snippet.njk"
