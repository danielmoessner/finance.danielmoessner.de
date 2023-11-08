from django.http import JsonResponse
from django.views import View

from apps.users.mixins import GetUserMixin


class IncomeAndExpenditureData(GetUserMixin, View):
    def get_queryset(self):
        return self.get_user().banking_depots.all()

    def get(self, request, pk):
        instance = self.get_queryset().get(pk=pk)

        data = instance.get_income_and_expenditure_data()

        return JsonResponse(data, safe=False)


class BalanceData(GetUserMixin, View):
    def get_queryset(self):
        return self.get_user().banking_depots.all()

    def get(self, request, pk):
        instance = self.get_queryset().get(pk=pk)

        data = instance.get_balance_data()

        return JsonResponse(data, safe=False)
