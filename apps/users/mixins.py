from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from apps.users.models import StandardUser


class GetUserMixin(LoginRequiredMixin):
    request: HttpRequest

    def get_user(self) -> StandardUser:
        user = self.request.user
        assert isinstance(user, StandardUser)
        return user
