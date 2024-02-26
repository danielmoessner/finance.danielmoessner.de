import json
from typing import Callable

from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string

from apps.users.models import StandardUser
from django.db import models

###
# Form Mixins
###
class CustomGetFormUserMixin:
    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        user = self.request.user
        return form_class(user, **self.get_form_kwargs())


class AjaxResponseMixin:
    get_context_data: Callable
    template_name: str
    request: HttpRequest

    def form_invalid(self, form):
        html = render_to_string(
            self.template_name, self.get_context_data(form=form), request=self.request
        )
        return HttpResponse(
            json.dumps({"valid": False, "html": html}), content_type="application/json"
        )

    def form_valid(self, form):
        form.save()
        return HttpResponse(
            json.dumps({"valid": True}), content_type="application/json"
        )


class GetFormWithUserMixin:
    get_user: Callable[[], StandardUser]
    get_form_class: Callable[[], type]
    get_form_kwargs: Callable[[], dict]

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        user = self.get_user()
        return form_class(user, **self.get_form_kwargs())


class GetFormWithDepotMixin:
    get_depot: Callable[[], models.Model]
    get_form_class: Callable[[], type]
    get_form_kwargs: Callable[[], dict]
    
    def get_form(self, form_class=None):
        depot = self.get_depot()
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(depot, **self.get_form_kwargs())


class GetFormWithDepotAndInitialDataMixin:
    def get_form(self, form_class=None):
        depot = self.get_depot()
        if form_class is None:
            form_class = self.get_form_class()
        if self.request.method == "GET":
            return form_class(
                depot, initial=self.request.GET, **self.get_form_kwargs().pop("initial")
            )
        return form_class(depot, **self.get_form_kwargs())


###
# Other Mixins
###
class TabContextMixin:
    def get_context_data(self, **kwargs):
        context = super(TabContextMixin, self).get_context_data(**kwargs)
        context["tab"] = self.request.GET.get("tab", "stats")
        return context


class CustomAjaxDeleteMixin:
    get_object: Callable[[], models.Model]

    def form_valid(self, form):
        object = self.get_object()
        object.delete()
        return HttpResponse(
            json.dumps({"valid": True}), content_type="application/json"
        )
