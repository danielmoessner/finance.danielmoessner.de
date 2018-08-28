from django.contrib import messages
from django.views import generic
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from finance.alternative.models import Alternative
from finance.alternative.models import Depot
# from finance.alternative.tasks import update_movies_task
from finance.core.utils import create_paginator

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from background_task.models import Task
from rest_framework.views import APIView
from datetime import timedelta
from datetime import datetime
import pandas as pd
import json


# messenger
def messenger(request, depot):
    if depot.movies.filter(update_needed=True).exists():
        hit = False
        tasks = Task.objects.filter(task_name="finance.alternative.tasks.update_movies_task")
        for task in tasks:
            depot_pk = json.loads(task.task_params)[0][0]
            if depot_pk == depot.pk:
                text = "One update is scheduled. You will be notified as soon as it succeeded."
                messages.info(request, text)
                hit = True
        if not hit:
            text = "New data is available. Hit the update button so that I can update everything."
            messages.info(request, text)
    else:
        text = "Everything is up to date."
        messages.success(request, text)


# views
class IndexView(generic.TemplateView):
    template_name = "alternative_index.njk"

    def get_context_data(self, **kwargs):
        # general
        context = super(IndexView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        context["depot"] = context["user"].alternative_depots.get(is_active=True)
        context["alternatives"] = context["depot"].alternatives.order_by("name")
        context["timespans"] = context["depot"].timespans.all()
        context["timespan"] = context["depot"].timespans.filter(is_active=True).first()
        # specific
        context["movie"] = context["depot"].get_movie()
        context["alternatives_movies"] = zip(context["alternatives"], context["depot"].movies.filter(
            alternative__in=context["alternatives"]).order_by("alternative__name"))
        # messages
        messenger(self.request, context["depot"])
        # return
        return context


class AlternativeView(generic.TemplateView):
    template_name = "alternative_alternative.njk"

    def get_context_data(self, **kwargs):
        # general
        context = super(AlternativeView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        context["depot"] = context["user"].alternative_depots.get(is_active=True)
        context["alternatives"] = context["depot"].alternatives.order_by("name").select_related("depot")
        context["timespans"] = context["depot"].timespans.all()
        context["timespan"] = context["depot"].timespans.filter(is_active=True).first()
        # specific
        context["alternative"] = context["depot"].alternatives.select_related("depot").get(slug=kwargs["slug"])
        context["movie"] = context["alternative"].get_movie()
        values = context["alternative"].values.order_by("-date", "-pk")
        context["values"], success = create_paginator(self.request.GET.get("values-page"), values, 10)
        context["console"] = "values" if success else "console-main"
        flows = context["alternative"].flows.order_by("-date", "-pk")
        context["flows"], success = create_paginator(self.request.GET.get("flows-page"), flows, 10)
        context["console"] = "flows" if success else "console-main"
        # messages
        messenger(self.request, context["depot"])
        # return
        return context


# functions
def update_movies(request):
    depot = request.user.alternative_depots.get(is_active=True)
    depot.update_movies()
    return HttpResponseRedirect(reverse_lazy("alternative:index"))


def reset_movies(request):
    depot = request.user.alternative_depots.get(is_active=True)
    depot.reset_movies(delete=True)
    return HttpResponseRedirect(reverse_lazy("alternative:index"))
