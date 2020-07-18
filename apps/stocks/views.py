from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from .models import Depot, Stock, Bank
from apps.core.views import CustomGetFormUserMixin, AjaxResponseMixin
from .forms import DepotForm


###
# Mixins
###
class CustomGetFormMixin:
    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        depot = self.request.user.crypto_depots.get(is_active=True)
        return form_class(depot, **self.get_form_kwargs())


class GetDepotMixin:
    def get_depot(self):
        return self.request.user.crypto_depots.filter(is_active=True).first()


###
# Depot: Detail, Create
###
class IndexView(generic.DetailView):
    template_name = 'stocks/index.j2'
    model = Depot


class CreateDepotView(LoginRequiredMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.CreateView):
    template_name = 'modules/form_snippet.njk'
    model = Depot
    form_class = DepotForm


###
# Stock: Detail
###
class StockView(generic.DetailView):
    template_name = 'stocks/stock.j2'
    model = Stock


###
# Bank: Detail
###
class BankView(generic.DetailView):
    template_name = 'stocks/bank.j2'
    model = Bank


###
# Flow:
###
pass


###
# Trade:
###
pass
