from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest

from apps.users.models import StandardUser


class GetUserMixin(LoginRequiredMixin):
    request: HttpRequest

    def get_user(self) -> StandardUser:
        user = self.request.user
        assert isinstance(user, StandardUser)
        return user
