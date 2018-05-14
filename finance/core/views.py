from django.views import generic

from .forms import DeleteForm


class CustomDeleteView(generic.View):
    def post(self, request, *args, **kwargs):
        form = DeleteForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        raise NotImplementedError()

    def form_invalid(self, form):
        raise NotImplementedError()
