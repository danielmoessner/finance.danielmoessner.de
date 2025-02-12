from django.views import generic

from apps.banking.models import Account, Category, Depot
from apps.banking.utils import get_latest_years
from apps.core.functional import list_sort
from apps.core.mixins import TabContextMixin
from apps.users.mixins import GetUserMixin


class IndexView(GetUserMixin, TabContextMixin, generic.DetailView):
    template_name = "banking/index.j2"
    model = Depot
    object: Depot

    def get_object(self, _=None) -> Depot | None:
        return self.get_user().get_active_banking_depot()

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context["user"] = self.get_user()
        if self.tab == "stats":
            context["stats"] = self.object.get_stats()
        if self.tab == "accounts":
            show_archived = self.request.GET.get("show_archived", False)
            accounts = self.object.accounts.all()
            if not show_archived:
                accounts = accounts.filter(is_archived=False)
            context["accounts"] = accounts.select_related("bucket")
        elif self.tab == "categories":
            categories = list(self.object.categories.all())
            categories = list_sort(
                categories, lambda c: c.get_latest_years_sum(), reverse=True
            )
            context["categories"] = categories
            context["years"] = get_latest_years(5)
        return context


class AccountView(GetUserMixin, TabContextMixin, generic.DetailView):
    template_name = "banking/account.j2"
    model = Account
    object: Account

    def get_queryset(self):
        return Account.objects.filter(depot__in=self.get_user().banking_depots.all())

    def get_show(self) -> int:
        show = self.request.GET.get("show", 30)
        return int(show)

    def get_context_show(self, show: int) -> str | None:
        if show >= self.object.changes.count():
            return None
        return str(show + 100)

    def get_context_data(self, **kwargs):
        context = super(AccountView, self).get_context_data(**kwargs)
        context["account"] = self.object
        if self.tab == "stats":
            context["stats"] = self.object.get_stats()
        if self.tab == "changes":
            show = self.get_show()
            context["changes"] = list(
                self.object.changes.order_by("-date", "-pk").select_related("category")[
                    :show
                ]
            )
            context["show"] = self.get_context_show(show)
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
