from django.contrib.auth.mixins import LoginRequiredMixin
from apps.alternative.models import Alternative, Depot
from apps.core.views import TabContextMixin
from django.views import generic


class IndexView(LoginRequiredMixin, TabContextMixin, generic.DetailView):
    template_name = 'alternative/index.j2'
    model = Depot

    def get_queryset(self):
        return self.request.user.alternative_depots.all()

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['alternatives'] = self.object.alternatives.order_by('name')
        context['stats'] = self.object.get_stats()
        return context


class AlternativeView(LoginRequiredMixin, TabContextMixin, generic.DetailView):
    template_name = 'alternative/alternative.j2'
    model = Alternative

    def get_queryset(self):
        return Alternative.objects.filter(depot__in=self.request.user.alternative_depots.all())

    def get_context_data(self, **kwargs):
        context = super(AlternativeView, self).get_context_data(**kwargs)
        context['depot'] = self.object.depot
        context['alternatives'] = context['depot'].alternatives.order_by('name').select_related('depot')
        context['flows_and_values'] = self.object.get_flows_and_values()
        context['stats'] = self.object.get_stats()
        return context
