from django.views import generic
from django.shortcuts import render
from finance.core.forms import DeleteForm


class CustomDeleteView(generic.View):
    def post(self, request, *args, **kwargs):
        form = DeleteForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form, **kwargs)

    def form_valid(self, form):
        raise NotImplementedError()

    def form_invalid(self, form, **kwargs):
        raise NotImplementedError()


def error_400_view(request, exception=None):
    return render(request, "error_templates/400.html")


def error_403_view(request, exception=None):
    return render(request, "error_templates/403.html")


def error_404_view(request, exception=None):
    return render(request, "error_templates/404.html")


def error_500_view(request, exception=None):
    return render(request, "error_templates/500.html")

