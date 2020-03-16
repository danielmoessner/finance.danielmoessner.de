from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.views import generic
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from finance.alternative.models import Alternative

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from background_task.models import Task
from rest_framework.views import APIView
import json


# messenger
def messenger(request, depot):
    if depot.movies.filter(update_needed=True).exists():
        hit = False
        tasks = Task.objects.filter(task_name='finance.alternative.tasks.update_movies_task')
        for task in tasks:
            depot_pk = json.loads(task.task_params)[0][0]
            if depot_pk == depot.pk:
                text = 'One update is scheduled. You will be notified as soon as it succeeded.'
                messages.info(request, text)
                hit = True
        if not hit:
            text = 'New data is available. Hit the update button so that I can update everything.'
            messages.info(request, text)
    else:
        text = 'Everything is up to date.'
        messages.success(request, text)


# views
class IndexView(generic.TemplateView):
    template_name = 'alternative/index.j2'

    def get_context_data(self, **kwargs):
        # general
        context = super(IndexView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        context['depot'] = context['user'].alternative_depots.get(is_active=True)
        context['alternatives'] = context['depot'].alternatives.order_by('name')
        context['timespans'] = context['depot'].timespans.all()
        context['timespan'] = context['depot'].timespans.filter(is_active=True).first()
        # specific
        context['movie'] = context['depot'].get_movie()
        context['alternatives_movies'] = zip(context['alternatives'], context['depot'].movies.filter(
            alternative__in=context['alternatives']).order_by('alternative__name'))
        # messages
        messenger(self.request, context['depot'])
        # return
        return context


class AlternativeView(PermissionRequiredMixin, generic.DetailView):
    template_name = 'alternative/alternative.j2'
    model = Alternative
    permission_denied_message = 'You have no permission to see this alternative.'

    def has_permission(self):
        return self.get_object().depot.user == self.request.user

    def get_context_data(self, **kwargs):
        # general
        context = super(AlternativeView, self).get_context_data(**kwargs)
        context['tab'] = self.request.GET.get('tab', 'stats')
        context['depot'] = self.object.depot
        context['alternatives'] = context['depot'].alternatives.order_by('name').select_related('depot')
        context['alternative'] = self.object
        context['flows_and_values'] = context['alternative'].get_flows_and_values()
        context['movie'] = context['alternative'].get_movie()
        context['stats'] = self.object.get_stats()
        # messages
        messenger(self.request, context['depot'])
        # return
        return context


# functions
def update_movies(request):
    depot = request.user.alternative_depots.get(is_active=True)
    depot.update_movies()
    return HttpResponseRedirect(reverse_lazy('alternative:index'))


def reset_movies(request):
    depot = request.user.alternative_depots.get(is_active=True)
    depot.reset_movies(delete=True)
    return HttpResponseRedirect(reverse_lazy('alternative:index'))


# API DATA
def json_data(pi, g=True, v=True, cr=True, twr=True, cs=True):
    labels = pi['d']

    datasets = list()
    if g:
        data_profit = dict()
        data_profit['label'] = 'Profit'
        data_profit['data'] = pi['g']
        data_profit['yAxisID'] = 'value'
        datasets.append(data_profit)
    if v:
        data_value = dict()
        data_value['label'] = 'Value'
        data_value['data'] = pi['v']
        data_value['yAxisID'] = 'value'
        datasets.append(data_value)
    if cr:
        data_cr = dict()
        data_cr['label'] = 'Current return'
        data_cr['data'] = map(lambda x: x*100, pi['cr'])
        data_cr['yAxisID'] = 'yield'
        datasets.append(data_cr)
    if twr:
        data_ttwr = dict()
        data_ttwr['label'] = 'Time weighted return'
        data_ttwr['data'] = map(lambda x: x*100, pi['twr'])
        data_ttwr['yAxisID'] = 'yield'
        datasets.append(data_ttwr)
    if cs:
        data_cs = dict()
        data_cs['label'] = 'Invested Capital'
        data_cs['data'] = pi['cs']
        data_cs['yAxisID'] = 'value'
        datasets.append(data_cs)
    data = dict()
    data['labels'] = labels
    data['datasets'] = datasets
    return Response(data)


class EverythingData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        user = request.user
        try:
            depot = user.alternative_depots.get(is_active=True)
        except ObjectDoesNotExist:
            depot = user.alternative_depots.first()
        try:
            timespan = depot.timespans.get(is_active=True)
        except ObjectDoesNotExist:
            timespan = None
        pi = depot.get_movie().get_data(timespan)
        return json_data(pi)


class CakeData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        user = request.user
        try:
            depot = user.alternative_depots.get(is_active=True)
        except ObjectDoesNotExist:
            depot = user.alternative_depots.first()
        alternatives = depot.alternatives.all()
        movies = depot.movies.filter(alternative__in=alternatives).select_related('alternative')
        datasets = list()
        labels = list()
        data = list()
        for movie in movies:
            try:
                picture = movie.pictures.latest('d')
            except ObjectDoesNotExist:
                continue
            value = picture.v
            if value and round(value, 2) != 0.00:
                labels.append(str(movie.alternative))
                data.append(value)
        data_and_labels = list(sorted(zip(data, labels)))
        labels = [l for d, l in data_and_labels]
        data = [abs(d) for d, l in data_and_labels]
        datasets_data = dict()
        datasets_data['data'] = data
        datasets.append(datasets_data)

        data = dict()
        data['datasets'] = datasets
        data['labels'] = labels
        return Response(data)


class AlternativeData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, slug, format=None):
        user = request.user
        try:
            depot = user.alternative_depots.get(is_active=True)
        except ObjectDoesNotExist:
            depot = user.alternative_depots.first()
        alternative = Alternative.objects.select_related('depot').get(slug=slug)
        try:
            timespan = depot.timespans.get(is_active=True)
        except ObjectDoesNotExist:
            timespan = None
        pi = alternative.get_movie().get_data(timespan)
        return json_data(pi)
