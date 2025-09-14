from django.views import generic

from apps.alternative.models import Alternative, Depot
from apps.core.mixins import TabContextMixin
from apps.users.mixins import GetUserMixin
from apps.users.models import StandardUser


class DetailDepotView(GetUserMixin, TabContextMixin, generic.DetailView):
    template_name = "alternative/index.j2"
    model = Depot
    object: Depot

    def get_object(self, _=None) -> Depot | None:
        user: StandardUser = self.get_user()  # type: ignore
        return user.get_active_alternative_depot()

    def get_context_data(self, **kwargs):
        context = super(DetailDepotView, self).get_context_data(**kwargs)
        alternatives = self.object.alternatives.order_by("name").select_related(
            "bucket"
        )
        show_archived = self.request.GET.get("show_archived", False)
        if not show_archived:
            alternatives = alternatives.filter(is_archived=False)
        context["alternatives"] = alternatives
        context["stats"] = self.object.get_stats()
        return context


class DetailAlternativeView(GetUserMixin, TabContextMixin, generic.DetailView):
    template_name = "alternative/alternative.j2"
    model = Alternative
    object: Alternative

    def get_queryset(self):
        return Alternative.objects.filter(
            depot__in=self.get_user().alternative_depots.all()
        )

    def get_context_data(self, **kwargs):
        context = super(DetailAlternativeView, self).get_context_data(**kwargs)
        context["depot"] = self.object.depot
        context["alternatives"] = (
            context["depot"].alternatives.order_by("name").select_related("depot")
        )
        context["flows_and_values"] = self.object.get_flows_and_values()
        context["stats"] = self.object.get_stats()
        return context
