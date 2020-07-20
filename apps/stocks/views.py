import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic
from .models import Depot, Stock, Bank
from apps.core.views import CustomGetFormUserMixin, AjaxResponseMixin
from .forms import DepotForm, DepotActiveForm, DepotSelectForm


###
# Mixins
###
class CustomGetFormMixin:
    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        depot = self.request.user.stock_depots.get(is_active=True)
        return form_class(depot, **self.get_form_kwargs())


class GetDepotMixin:
    def get_depot(self):
        return self.request.user.stock_depots.filter(is_active=True).first()


###
# Depot: Detail, Create, Edit, Delete, SetActive
###
class IndexView(generic.DetailView):
    template_name = 'stocks/index.j2'
    model = Depot

    def get_queryset(self):
        return self.request.user.stock_depots.all()


class CreateDepotView(LoginRequiredMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.CreateView):
    template_name = 'modules/form_snippet.njk'
    model = Depot
    form_class = DepotForm


class EditDepotView(LoginRequiredMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.UpdateView):
    model = Depot
    form_class = DepotForm
    template_name = "modules/form_snippet.njk"


class DeleteDepotView(LoginRequiredMixin, CustomGetFormUserMixin, AjaxResponseMixin, generic.FormView):
    model = Depot
    template_name = "modules/form_snippet.njk"
    form_class = DepotSelectForm

    def form_valid(self, form):
        depot = form.cleaned_data["depot"]
        user = depot.user
        depot.delete()
        if user.stock_depots.count() <= 0:
            user.save()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


class SetActiveDepotView(LoginRequiredMixin, generic.View):
    http_method_names = ['get', 'head', 'options']

    def get(self, request, pk, *args, **kwargs):
        depot = get_object_or_404(self.request.user.stock_depots.all(), pk=pk)
        form = DepotActiveForm(data={'is_active': True}, instance=depot)
        if form.is_valid():
            form.save()
        url = '{}?tab=stocks'.format(reverse_lazy('users:settings', args=[self.request.user.pk]))
        return HttpResponseRedirect(url)


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
