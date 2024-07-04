from django.utils import timezone
from django.views import generic

from apps.banking.models import Account, Category, Change, Depot
from apps.banking.utils import get_latest_years
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
            context["accounts"] = self.object.accounts.order_by("name").select_related(
                "bucket"
            )
        elif self.tab == "categories":
            context["categories"] = self.object.categories.order_by("name")
            context["years"] = get_latest_years(5)
        return context


class AccountView(GetUserMixin, TabContextMixin, generic.DetailView):
    template_name = "banking/account.j2"
    model = Account
    object: Account

    def get_queryset(self):
        return Account.objects.filter(depot__in=self.get_user().banking_depots.all())

    def get_year(self) -> int:
        current_year = str(timezone.now().year)
        year = self.request.GET.get("year", current_year)
        return int(year)

    def get_context_year(self, year: int, changes: list[Change]) -> str | None:
        if len(changes) == 0:
            return str(year - 1)
        return str(int(year) - 1) if changes[-1].date.year == int(year) else None

    def get_context_data(self, **kwargs):
        context = super(AccountView, self).get_context_data(**kwargs)
        context["account"] = self.object
        if self.tab == "stats":
            context["stats"] = self.object.get_stats()
        if self.tab == "changes":
            year = self.get_year()
            context["changes"] = list(
                self.object.changes.filter(date__year__gte=str(year))
                .order_by("-date", "-pk")
                .select_related("category")
            )
            context["year"] = self.get_context_year(year, context["changes"])
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
