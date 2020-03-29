from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from apps.alternative.models import Alternative
from apps.alternative.models import Depot
from apps.core.views import TabContextMixin


# views
class IndexView(LoginRequiredMixin, TabContextMixin, generic.DetailView):
    template_name = 'alternative/index.j2'
    model = Depot
    permission_denied_message = 'You have no permission to see this depot.'

    def get_queryset(self):
        return self.request.user.alternative_depots.all()

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        # general
        context['alternatives'] = self.object.alternatives.select_related('latest_picture').order_by('name')
        # specific
        context['movie'] = self.object.get_movie()
        context['stats'] = context['movie'].get_stats()
        context['pictures'] = context['movie'].get_pictures()
        # return
        return context


class AlternativeView(LoginRequiredMixin, TabContextMixin, generic.DetailView):
    template_name = 'alternative/alternative.j2'
    model = Alternative
    permission_denied_message = 'You have no permission to see this alternative.'

    def get_queryset(self):
        return Alternative.objects.filter(depot__in=self.request.user.alternative_depots.all())

    def get_context_data(self, **kwargs):
        context = super(AlternativeView, self).get_context_data(**kwargs)
        # general
        context['depot'] = self.object.depot
        context['alternatives'] = context['depot'].alternatives.order_by('name').select_related('depot')
        context['flows_and_values'] = self.object.get_flows_and_values()
        context['movie'] = self.object.get_movie()
        context['stats'] = context['movie'].get_stats()
        context['pictures'] = context['movie'].get_pictures()
        # return
        return context


# functions
def reset_movies(request):
    depot = request.user.alternative_depots.get(is_active=True)
    depot.reset_movies(delete=True)
    return HttpResponseRedirect(reverse_lazy('alternative:index', args=[depot.pk]))
