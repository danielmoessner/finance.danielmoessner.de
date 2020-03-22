from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic.base import ContextMixin
from django.views import generic
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from apps.banking.models import Category
from apps.banking.models import Account
from apps.banking.models import Depot
from apps.core.views import TabContextMixin

from rest_framework.response import Response
from rest_framework.generics import GenericAPIView


# views
class IndexView(UserPassesTestMixin, TabContextMixin, generic.DetailView):
    template_name = "banking/index.njk"
    model = Depot
    permission_denied_message = 'You have no permission to see this depot.'

    def test_func(self):
        return self.get_object().user == self.request.user

    def get_context_data(self, **kwargs):
        # general
        context = super(IndexView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        context["accounts"] = self.object.accounts.order_by("name")
        context["categories"] = self.object.categories.order_by("name")
        context["timespans"] = self.object.timespans.all()
        context["timespan"] = self.object.timespans.filter(is_active=True).first()
        # specific
        context['stats'] = self.object.get_stats()
        context['accounts'] = self.object.accounts.order_by('name')
        context['categories'] = self.object.categories.order_by('name')
        # return
        return context


class AccountView(UserPassesTestMixin, TabContextMixin, generic.DetailView):
    template_name = "banking/account.njk"
    model = Account

    def test_func(self):
        return self.get_object().depot.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super(AccountView, self).get_context_data(**kwargs)
        context["depot"] = self.object.depot
        context["accounts"] = context["depot"].accounts.order_by("name")
        context["categories"] = context["depot"].categories.order_by("name")
        context["timespans"] = context["depot"].timespans.all()
        context["timespan"] = context["depot"].timespans.filter(is_active=True).first()
        context["account"] = self.object
        context["stats"] = self.object.get_stats()
        context["changes"] = self.object.changes.order_by("-date", "-pk").select_related("category")
        return context


class CategoryView(UserPassesTestMixin, TabContextMixin, generic.DetailView):
    template_name = "banking/category.njk"
    model = Category

    def test_func(self):
        return self.get_object().depot.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super(CategoryView, self).get_context_data(**kwargs)
        context["depot"] = self.object.depot
        context["accounts"] = context["depot"].accounts.order_by("name")
        context["categories"] = context["depot"].categories.order_by("name")
        context["timespans"] = context["depot"].timespans.all()
        context["timespan"] = context["depot"].timespans.filter(is_active=True).first()
        context["category"] = self.object
        context['stats'] = self.object.get_stats()
        context["changes"] = self.object.changes.order_by("-date", "-pk").select_related("account")
        return context


# functions
def reset_balances(request):
    depot = request.user.banking_depots.get(is_active=True)
    depot.set_balances_to_none()
    return HttpResponseRedirect(reverse_lazy("banking:index", args=[depot.pk]))


# chart api
class IncomeAndExpenditureData(GenericAPIView):
    def get_queryset(self):
        user = self.request.user
        return user.banking_depots.all()

    def get(self, request, pk):
        instance = self.get_object()

        data = instance.get_income_and_expenditure_data()

        return Response(data)


class BalanceData(GenericAPIView):
    def get_queryset(self):
        user = self.request.user
        return user.banking_depots.all()

    def get(self, request, pk):
        instance = self.get_object()

        data = instance.get_balance_data()

        return Response(data)
