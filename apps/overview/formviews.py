from django.views import generic

from apps.core.mixins import (
    AjaxResponseMixin,
    CustomAjaxDeleteMixin,
    GetFormWithUserMixin,
)
from apps.overview.forms import BucketForm
from apps.overview.models import Bucket
from apps.users.mixins import GetUserMixin


class AddBucketView(
    GetUserMixin,
    GetFormWithUserMixin,
    AjaxResponseMixin,
    generic.CreateView,
):
    model = Bucket
    form_class = BucketForm
    template_name = "symbols/form_snippet.j2"


class EditBucketView(
    GetUserMixin,
    GetFormWithUserMixin,
    AjaxResponseMixin,
    generic.UpdateView,
):
    model = Bucket
    form_class = BucketForm
    template_name = "symbols/form_snippet.j2"

    def get_queryset(self):
        return Bucket.objects.filter(user=self.get_user())


class DeleteBucketView(GetUserMixin, CustomAjaxDeleteMixin, generic.DeleteView):
    model = Bucket
    template_name = "symbols/delete_snippet.j2"

    def get_queryset(self):
        return Bucket.objects.filter(user=self.get_user())
