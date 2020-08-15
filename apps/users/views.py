from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.views import generic
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from apps.users.models import StandardUser
from apps.users.forms import CreateStandardUserForm
from apps.core.mixins import TabContextMixin


class RedirectView(generic.RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            user = self.request.user
            front_page = user.front_page
            if front_page == "BANKING":
                return reverse_lazy("banking:index", args=[user.get_active_banking_depot_pk()])
            elif front_page == "CRYPTO":
                return reverse_lazy("crypto:index")
            elif front_page == "ALTERNATIVE":
                return reverse_lazy("alternative:index", args=[user.get_active_alternative_depot_pk()])
            else:
                return reverse_lazy("users:settings", args=[user.pk])
        else:
            return reverse_lazy('users:signin')


class SignUpView(generic.CreateView):
    form_class = CreateStandardUserForm
    success_url = reverse_lazy('users:redirect')
    template_name = 'users/signup.j2'


class SignInView(LoginView):
    redirect_authenticated_user = True
    template_name = 'users/login.j2'


class SignOutView(LogoutView):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('users:redirect')


class IndexView(UserPassesTestMixin, TabContextMixin, generic.DetailView):
    template_name = "users/index.j2"
    model = StandardUser

    def test_func(self):
        return self.get_object() == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["banking_depots"] = self.object.banking_depots.all()
        context["crypto_depots"] = self.object.crypto_depots.all()
        context["alternative_depots"] = self.object.alternative_depots.all()
        context['stock_depots'] = self.object.stock_depots.all()
        return context


def init_banking(request, pk):
    user = request.user
    depot = user.create_random_banking_data()
    message = "{} was created.".format(depot.name)
    messages.success(request, message)
    url = '{}?tab=banking'.format(reverse_lazy("users:settings", args=[user.pk]))
    return HttpResponseRedirect(url)


def init_crypto(request, pk):
    user = request.user
    depot = user.create_random_crypto_data()
    message = "{} was created.".format(depot.name)
    messages.success(request, message)
    url = '{}?tab=crypto'.format(reverse_lazy("users:settings", args=[user.pk]))
    return HttpResponseRedirect(url)


def init_alternative(request, pk):
    user = request.user
    depot = user.create_random_alternative_data()
    message = "{} was created.".format(depot.name)
    messages.success(request, message)
    url = '{}?tab=alternative'.format(reverse_lazy("users:settings", args=[user.pk]))
    return HttpResponseRedirect(url)
