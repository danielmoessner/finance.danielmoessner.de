from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic.base import ContextMixin
from django.views import generic
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from finance.alternative.models import Alternative
from finance.alternative.models import Depot


# mixins
class TabContextMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super(TabContextMixin, self).get_context_data(**kwargs)
        context['tab'] = self.request.GET.get('tab', 'stats')
        return context


# views
class IndexView(PermissionRequiredMixin, TabContextMixin, generic.DetailView):
    template_name = 'alternative/index.j2'
    model = Depot
    permission_denied_message = 'You have no permission to see this depot.'

    def has_permission(self):
        return self.get_object().user == self.request.user

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


class AlternativeView(PermissionRequiredMixin, TabContextMixin, generic.DetailView):
    template_name = 'alternative/alternative.j2'
    model = Alternative
    permission_denied_message = 'You have no permission to see this alternative.'

    def has_permission(self):
        return self.get_object().depot.user == self.request.user

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
    return HttpResponseRedirect(reverse_lazy('alternative:index'))
