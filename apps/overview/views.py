from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.mixins import TabContextMixin
from django.views import generic


# views
class IndexView(LoginRequiredMixin, TabContextMixin, generic.TemplateView):
    template_name = "overview/index.j2"

    def get_stats(self):
        total = 0
        for depot in self.request.user.get_all_active_depots():
            total += float(depot.get_value())
        return {
            'Total': round(total, 2)
        }

    def get_queryset(self):
        return self.request.user.banking_depots.all()

    def get_context_data(self, **kwargs):
        # general
        context = super(IndexView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        # specific
        context['stats'] = self.get_stats()
        # return
        return context
