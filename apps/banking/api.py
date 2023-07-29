from django.http import JsonResponse
from django.views import View


class IncomeAndExpenditureData(View):
    def get_queryset(self):
        user = self.request.user
        return user.banking_depots.all()

    def get(self, request, pk):
        instance = self.get_queryset().get(pk=pk)

        data = instance.get_income_and_expenditure_data()

        return JsonResponse(data, safe=False)


class BalanceData(View):
    def get_queryset(self):
        user = self.request.user
        return user.banking_depots.all()

    def get(self, request, pk):
        instance = self.get_queryset().get(pk=pk)

        data = instance.get_balance_data()

        return JsonResponse(data, safe=False)
