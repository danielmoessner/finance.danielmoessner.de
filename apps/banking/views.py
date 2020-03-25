from django.views import generic

from apps.banking.models import Category, Account, Depot
from apps.core.views import TabContextMixin


# views
class IndexView(TabContextMixin, generic.DetailView):
    template_name = "banking/index.njk"
    model = Depot

    def get_queryset(self):
        return self.request.user.banking_depots.all()

    def get_context_data(self, **kwargs):
        # general
        context = super(IndexView, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        context["accounts"] = self.object.accounts.order_by("name")
        context["categories"] = self.object.categories.order_by("name")
        # specific
        context['stats'] = self.object.get_stats()
        context['accounts'] = self.object.accounts.order_by('name')
        context['categories'] = self.object.categories.order_by('name')
        # return
        return context


class AccountView(TabContextMixin, generic.DetailView):
    template_name = "banking/account.njk"
    model = Account

    def get_queryset(self):
        return Account.objects.filter(depot__in=self.request.user.banking_depots.all())

    def get_context_data(self, **kwargs):
        context = super(AccountView, self).get_context_data(**kwargs)
        context["depot"] = self.object.depot
        context["accounts"] = context["depot"].accounts.order_by("name")
        context["categories"] = context["depot"].categories.order_by("name")
        context["account"] = self.object
        context["stats"] = self.object.get_stats()
        context["changes"] = self.object.changes.order_by("-date", "-pk").select_related("category")
        return context


class CategoryView(TabContextMixin, generic.DetailView):
    template_name = "banking/category.njk"
    model = Category

    def get_queryset(self):
        return Category.objects.filter(depot__in=self.request.user.banking_depots.all())

    def get_context_data(self, **kwargs):
        context = super(CategoryView, self).get_context_data(**kwargs)
        context["depot"] = self.object.depot
        context["accounts"] = context["depot"].accounts.order_by("name")
        context["categories"] = context["depot"].categories.order_by("name")
        context["category"] = self.object
        context['stats'] = self.object.get_stats()
        context["changes"] = self.object.changes.order_by("-date", "-pk").select_related("account")
        return context
