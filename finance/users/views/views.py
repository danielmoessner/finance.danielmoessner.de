from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import logout as logout_user
from django.contrib.auth import login as login_user
from django.contrib.auth import authenticate
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.utils.html import strip_tags
from django.urls import reverse_lazy
from django.views import generic

from finance.users.forms import CreateStandardUserForm
from finance.users.forms import UpdateCryptoStandardUserForm
from finance.users.forms import UpdateGeneralStandardUserForm
from finance.users.forms import UpdateStandardUserForm
from finance.banking.models import Depot as BankingDepot
from finance.banking.models import init_banking as banking_init_banking
from finance.crypto.models import init_crypto as crypto_init_crypto
from finance.crypto.models import Depot as CryptoDepot


def signup(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse_lazy("users:settings", args=[request.user.slug, ]))

    if request.method == "POST":
        form = CreateStandardUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login_user(request, user)
            return HttpResponseRedirect(reverse_lazy("users:settings", args=[request.user.slug, ]))
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
        front_page = request.user.front_page
        if front_page == "BANKING":
            url = reverse_lazy("banking:index", args=[request.user.slug])
        elif front_page == "CRYPTO":
            url = reverse_lazy("crypto:index", args=[request.user.slug])
        else:
            url = reverse_lazy("users:settings")
        return HttpResponseRedirect(url)

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login_user(request, user)
            return HttpResponseRedirect(reverse_lazy("users:login"))
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
        context["edit_user_form"] = UpdateStandardUserForm(instance=self.request.user)
        context["edit_user_password_form"] = PasswordChangeForm(user=self.request.user)
        context["edit_user_general_form"] = UpdateGeneralStandardUserForm(
            instance=self.request.user)

        # banking
        context["banking_depots"] = context["user"].banking_depots.all()
        # crypto
        context["crypto_depots"] = context["user"].crypto_depots.all()
        context["edit_user_crypto_form"] = UpdateCryptoStandardUserForm(instance=self.request.user)
        return context


def init_banking(request, slug):
    user = request.user
    banking_init_banking(user)
    user.banking_is_active = True
    user.save()
    return HttpResponseRedirect(reverse_lazy("users:settings", args=[slug, ]))


def init_crypto(request, slug):
    user = request.user
    crypto_init_crypto(user)
    user.crypto_is_active = True
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
