from django.urls import path

from apps.overview import views

app_name = "overview"

urlpatterns = [
    path("dashboard/", views.IndexView.as_view(), name="index"),
    path("api/data/", views.DataApiView.as_view(), name="api_data"),
    # bucket
    path("buckets/add/", views.AddBucketView.as_view(), name="add_bucket"),
    path("buckets/<int:pk>/edit/", views.EditBucketView.as_view(), name="edit_bucket"),
    path("buckets/<int:pk>/delete/", views.DeleteBucketView.as_view(), name="delete_bucket"),
]
