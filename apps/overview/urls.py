from apps.overview import views
from django.urls import path

app_name = "overview"

urlpatterns = [
    path("dashboard/", views.IndexView.as_view(), name="index"),
    path('api/data/', views.DataApiView.as_view(), name='api_data'),
]
