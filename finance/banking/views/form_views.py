from django.views import generic
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from finance.banking.views.views import AccountView
from finance.banking.views.views import IndexView
from finance.core.views.views import CustomDeleteView
from finance.banking.models import Timespan
from finance.banking.models import Category
from finance.banking.models import Account
from finance.banking.models import Change
from finance.banking.forms import CreateTimespanForm
from finance.banking.forms import CreateAccountForm
from finance.banking.forms import EditAccountForm
from finance.banking.forms import CreateChangeForm
from finance.banking.forms import CreateCategoryForm
from finance.banking.forms import EditCategoryForm
from finance.banking.forms import EditChangeForm
from finance.core.utils import form_invalid_universal


# ACCOUNT
class IndexCreateAccountView(IndexView, generic.CreateView):
    form_class = CreateAccountForm
    model = Account

    def form_valid(self, form):
        account = form.save(commit=False)
        account.depot = self.request.user.banking_depots.get(is_active=True)
        account.save()
        success_url = reverse_lazy("banking:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="Account could not be created.")


class IndexEditAccountView(IndexView):
    def post(self, request, *args, **kwargs):
        form = EditAccountForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        account_pk = form.cleaned_data["pk"]
        account = Account.objects.get(pk=account_pk)
        account.name = form.cleaned_data["name"]
        account.save()
        success_url = reverse_lazy("banking:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors", heading="Account could not be edited.")


class IndexDeleteAccountView(IndexView, CustomDeleteView):
    def form_valid(self, form):
        account_pk = form.cleaned_data["pk"]
        account = Account.objects.get(pk=account_pk)
        account.delete()
        success_url = reverse_lazy("banking:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, **kwargs):
        return form_invalid_universal(self, form, "errors",
                                      heading="Account could not be deleted.", **kwargs)


# CATEGORY
class IndexCreateCategoryView(IndexView, generic.CreateView):
    form_class = CreateCategoryForm
    model = Category

    def form_valid(self, form):
        category = form.save(commit=False)
        category.depot = self.request.user.banking_depots.get(is_active=True)
        category.save()
        success_url = reverse_lazy("banking:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="Category could not be created.")


class IndexEditCategoryView(IndexView):
    def post(self, request, *args, **kwargs):
        form = EditCategoryForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        category = form.save(commit=False)
        category.pk = form.cleaned_data["pk"]
        category.depot = self.request.user.banking_depots.get(is_active=True)
        category.save()
        success_url = reverse_lazy("banking:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="Category could not be edited.")


class IndexDeleteCategoryView(IndexView, CustomDeleteView):
    def form_valid(self, form):
        category_pk = form.cleaned_data["pk"]
        category = Category.objects.get(pk=category_pk)
        category.delete()
        success_url = reverse_lazy("banking:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, **kwargs):
        return form_invalid_universal(self, form, "errors",
                                      heading="Account could not be deleted.", **kwargs)


# CHANGE
class IndexCreateChangeView(IndexView, generic.CreateView):
    form_class = CreateChangeForm
    model = Change

    def form_valid(self, form):
        change = form.save()
        success_url = reverse_lazy("banking:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="Change could not be created.")


class AccountCreateChangeView(AccountView, generic.CreateView):
    form_class = CreateChangeForm
    model = Change

    def form_valid(self, form):
        change = form.save()
        account = change.account
        success_url = reverse_lazy("banking:account", args=[self.request.user.slug, account.slug])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="Change could not be created.")


class AccountEditChangeView(AccountView):
    def post(self, request, *args, **kwargs):
        form = EditChangeForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form, **kwargs)

    def form_valid(self, form):
        change = form.save(commit=False)
        change.pk = form.cleaned_data["pk"]
        change.save()
        account = change.account
        success_url = reverse_lazy("banking:account", args=[self.request.user.slug, account.slug])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, **kwargs):
        return form_invalid_universal(self, form, "errors",
                                      heading="Change could not be edited.", **kwargs)


class AccountDeleteChangeView(AccountView, CustomDeleteView):
    def form_valid(self, form):
        change_pk = form.cleaned_data["pk"]
        change = Change.objects.get(pk=change_pk)
        change.delete()
        account = change.account
        success_url = reverse_lazy("banking:account", args=[self.request.user.slug, account.slug])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, **kwargs):
        return form_invalid_universal(self, form, "errors",
                                      heading="Change could not be deleted.", **kwargs)


# TIMESPAN
class IndexCreateTimespanView(IndexView, generic.CreateView):
    form_class = CreateTimespanForm
    model = Timespan

    def form_valid(self, form):
        timespan = form.save(commit=False)
        timespan.depot = self.request.user.banking_depots.get(is_active=True)
        timespan.is_active = False
        timespan.save()
        success_url = reverse_lazy("banking:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="Timespan could not be created.")


class IndexDeleteTimespanView(IndexView, CustomDeleteView):
    def form_valid(self, form):
        timespan_pk = form.cleaned_data["pk"]
        timespan = Timespan.objects.get(pk=timespan_pk)
        if timespan.is_active:
            form_invalid_universal(self, form, "errors",
                                   heading="Timespan could not be deleted, because it's still "
                                           "active.",
                                   **self.request.kwargs)
        timespan.delete()
        success_url = reverse_lazy("banking:index", args=[self.request.user.slug, ])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, **kwargs):
        return form_invalid_universal(self, form, "errors",
                                      heading="Timespan could not be deleted.", **kwargs)
