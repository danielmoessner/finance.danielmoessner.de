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
from finance.banking.forms import UpdateActiveOnTimespanForm
from finance.banking.forms import CreateTimespanForm
from finance.banking.forms import CreateAccountForm
from finance.banking.forms import UpdateAccountForm
from finance.banking.forms import CreateChangeForm
from finance.banking.forms import CreateCategoryForm
from finance.banking.forms import UpdateCategoryForm
from finance.banking.forms import UpdateChangeForm
from finance.core.utils import form_invalid_universal


# ACCOUNT
class IndexCreateAccountView(IndexView, generic.CreateView):
    form_class = CreateAccountForm
    model = Account

    def form_valid(self, form):
        account = form.save(commit=False)
        account.depot = self.request.user.banking_depots.get(is_active=True)
        account.save()
        success_url = reverse_lazy("banking:index")
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="Account could not be created.")


class IndexUpdateAccountView(IndexView):
    def post(self, request, *args, **kwargs):
        form = UpdateAccountForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        account_pk = form.cleaned_data["pk"]
        account = Account.objects.get(pk=account_pk)
        account.name = form.cleaned_data["name"]
        account.save()
        success_url = reverse_lazy("banking:index")
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors", heading="Account could not be edited.")


class IndexDeleteAccountView(IndexView, CustomDeleteView):
    def form_valid(self, form):
        account_pk = form.cleaned_data["pk"]
        account = Account.objects.get(pk=account_pk)
        account.delete()
        success_url = reverse_lazy("banking:index")
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
        success_url = reverse_lazy("banking:index")
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="Category could not be created.")


class IndexUpdateCategoryView(IndexView):
    def post(self, request, *args, **kwargs):
        form = UpdateCategoryForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        category = form.save(commit=False)
        category.pk = form.cleaned_data["pk"]
        category.depot = self.request.user.banking_depots.get(is_active=True)
        category.save()
        success_url = reverse_lazy("banking:index")
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="Category could not be edited.")


class IndexDeleteCategoryView(IndexView, CustomDeleteView):
    def form_valid(self, form):
        category_pk = form.cleaned_data["pk"]
        category = Category.objects.get(pk=category_pk)
        category.delete()
        success_url = reverse_lazy("banking:index")
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
        success_url = reverse_lazy("banking:index")
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
        success_url = reverse_lazy("banking:account", args=[account.slug])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="Change could not be created.")


class AccountUpdateChangeView(AccountView):
    def post(self, request, *args, **kwargs):
        form = UpdateChangeForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form, **kwargs)

    def form_valid(self, form):
        change = form.save(commit=False)
        change.pk = form.cleaned_data["pk"]
        change.save()
        account = change.account
        success_url = reverse_lazy("banking:account", args=[account.slug])
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
        success_url = reverse_lazy("banking:account", args=[account.slug])
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
        success_url = reverse_lazy("banking:index")
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form):
        return form_invalid_universal(self, form, "errors",
                                      heading="Timespan could not be created.")


class IndexUpdateActiveOnTimespanView(IndexView):
    def post(self, request, *args, **kwargs):
        form = UpdateActiveOnTimespanForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.request.user.banking_depots.get(is_active=True).timespans.update(is_active=False)
        timespan_pk = form.cleaned_data["pk"]
        Timespan.objects.filter(pk=timespan_pk).update(is_active=True)
        success_url = reverse_lazy("banking:index")
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
        success_url = reverse_lazy("banking:index")
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, **kwargs):
        return form_invalid_universal(self, form, "errors",
                                      heading="Timespan could not be deleted.", **kwargs)
