from django.contrib.auth import logout as logout_user
from django.contrib.auth import login as login_user
from django.contrib.auth import authenticate
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.utils.html import strip_tags
from django.urls import reverse_lazy
from django.views import generic

from finance.users.forms import AddStandardUserForm
from finance.banking.models import Depot as BankingDepot
from finance.banking.models import init_banking as banking_init_banking
from finance.crypto.models import Depot as CryptoDepot


def signup(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse_lazy("users:settings", args=[request.user.slug, ]))

    if request.method == "POST":
        form = AddStandardUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login_user(request, user)
            return redirect("users:settings", args=[request.user.slug, ])
        else:
            errors = list()
            for field in form:
                errors.append(strip_tags(field.errors).replace(".", ". ").replace("  ", " "))
            errors.remove("")
            return render(request, "users_signup.njk", {"errors": errors})
    else:
        return render(request, "users_signup.njk")


def login(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse_lazy("users:settings", args=[request.user.slug, ]))

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login_user(request, user)
            return HttpResponseRedirect(reverse_lazy("users:settings", args=[request.user.slug, ]))
        else:
            errors = list()
            errors.append("This combination of username and password doesn't exist")
            return render(request, "users_login.njk", {"errors": errors})
    else:
        return render(request, "users_login.njk")


def logout(request, slug):
    logout_user(request)
    return redirect("users:login")


class SettingsView(generic.TemplateView):
    template_name = "users_settings.njk"

    def get_context_data(self, **kwargs):
        context = dict()
        context["user"] = self.request.user

        context["currencies"] = context["user"]._meta.get_field("currency").choices
        context["date_formats"] = context["user"]._meta.get_field("date_format").choices
        context["currencies"] = (self.request.user.currency, context["currencies"])
        context["date_formats"] = (self.request.user.date_format, context["date_formats"])
        context["rounded_numbers"] = context["user"].rounded_numbers

        context["banking_depots"] = context["user"].banking_depots.all()

        context["crypto_depots"] = context["user"].crypto_depots.all()

        return context


def init_banking(request, slug):
    user = request.user
    banking_init_banking(user)
    user.banking_active = True
    user.save()
    return HttpResponseRedirect(reverse_lazy("users:settings", args=[slug, ]))


def set_banking_depot_active(request, slug, pk):
    depot_pk = int(pk)
    depot = BankingDepot.objects.get(pk=depot_pk)
    request.user.set_banking_depot_active(depot)
    return HttpResponseRedirect(reverse_lazy("users:settings", args=[request.user.slug, ]))


def set_crypto_depot_active(request, slug, pk):
    depot_pk = int(pk)
    depot = CryptoDepot.objects.get(pk=depot_pk)
    request.user.set_crypto_depot_active(depot)
    return HttpResponseRedirect(reverse_lazy("users:settings", args=[request.user.slug, ]))
