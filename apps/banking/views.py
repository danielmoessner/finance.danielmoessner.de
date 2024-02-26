from django.views import generic

from apps.banking.models import Account, Category, Depot
from apps.core.mixins import TabContextMixin
from apps.users.mixins import GetUserMixin


class IndexView(GetUserMixin, TabContextMixin, generic.DetailView):
    template_name = "banking/index.j2"
    model = Depot
    object: Depot

    def get_object(self, _=None) -> Depot | None:
        return self.get_user().get_active_banking_depot()

    def get_context_data(self, **kwargs):
        # general
        context = super(IndexView, self).get_context_data(**kwargs)
        context["user"] = self.get_user()
        # specific
        context["stats"] = self.object.get_stats()
        context["accounts"] = self.object.accounts.order_by("name").select_related(
            "bucket"
        )
        context["categories"] = self.object.categories.order_by("name")
        # return
        return context


class AccountView(GetUserMixin, TabContextMixin, generic.DetailView):
    template_name = "banking/account.j2"
    model = Account
    object: Account

    def get_queryset(self):
        return Account.objects.filter(depot__in=self.get_user().banking_depots.all())

    def get_context_data(self, **kwargs):
        context = super(AccountView, self).get_context_data(**kwargs)
        context["depot"] = self.object.depot
        context["account"] = self.object
        context["stats"] = self.object.get_stats()
        context["changes"] = self.object.changes.order_by(
            "-date", "-pk"
        ).select_related("category")
        return context


class CategoryView(GetUserMixin, TabContextMixin, generic.DetailView):
    template_name = "banking/category.j2"
    model = Category
    object: Category

    def get_queryset(self):
        return Category.objects.filter(depot__in=self.get_user().banking_depots.all())

    def get_context_data(self, **kwargs):
        context = super(CategoryView, self).get_context_data(**kwargs)
        context["depot"] = self.object.depot
        context["category"] = self.object
        context["stats"] = self.object.get_stats()
        context["changes"] = self.object.changes.order_by(
            "-date", "-pk"
        ).select_related("account")
        return context
