from django.http import HttpRequest

from apps.users.models import StandardUser


class GetDepotMixin:
    request: HttpRequest

    def get_depot(self):
        user: StandardUser = self.request.user  # type: ignore
        return self.request.user.stock_depots.filter(is_active=True).first()
