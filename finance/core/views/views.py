from django.views import generic
from django.shortcuts import render
from django.utils.html import strip_tags
from finance.core.forms import DeleteForm
from django.views.generic.edit import FormMixin
from django.contrib import messages


# mixins
class CustomInvalidFormMixin(FormMixin):
    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        message = ["Form Error(s):"]
        for field in form:
            if field.errors:
                text = "{}: {}".format(field.label, strip_tags(field.errors))
                message.append(text)
        message = "<br>".join(message)
        messages.warning(self.request, message)
        return self.render_to_response(self.get_context_data(edit_user_form=form))


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


# error views
def error_400_view(request, exception=None):
    return render(request, "error_templates/400.html")


def error_403_view(request, exception=None):
    return render(request, "error_templates/403.html")


def error_404_view(request, exception=None):
    return render(request, "error_templates/404.html")


def error_500_view(request, exception=None):
    return render(request, "error_templates/500.html")

