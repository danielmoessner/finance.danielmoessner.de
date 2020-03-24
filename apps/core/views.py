from django.views.generic.base import ContextMixin
from django.template.loader import render_to_string
from apps.core.forms import DeleteForm
from django.utils.html import strip_tags
from django.contrib import messages
from django.views import generic
from django.http import HttpResponse

import json


# mixins
class TabContextMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super(TabContextMixin, self).get_context_data(**kwargs)
        context['tab'] = self.request.GET.get('tab', 'stats')
        return context


class CustomAjaxDeleteMixin(object):
    def delete(self, request, *args, **kwargs):
        object = self.get_object()
        object.delete()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


class CustomAjaxFormMixin(object):
    def form_invalid(self, form):
        html = render_to_string(self.template_name, self.get_context_data(form=form),
                                request=self.request)
        return HttpResponse(json.dumps({"valid": False, "html": html}),
                            content_type="application/json")

    def form_valid(self, form):
        form.save()
        return HttpResponse(json.dumps({"valid": True}), content_type="application/json")


class CustomInvalidFormMixin(object):
    def form_invalid(self, form):
        message = ["Form Error(s):"]
        for field in form:
            if field.errors:
                text = "{}: {}".format(field.label, strip_tags(field.errors))
                message.append(text)
        message = "<br>".join(message)
        messages.warning(self.request, message)
        return self.render_to_response(self.get_context_data(form=form))


# views
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
