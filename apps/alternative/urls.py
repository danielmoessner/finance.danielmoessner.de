from django.urls import path

from apps.alternative import views

app_name = "alternative"

urlpatterns = [
    # depot
    path("depots/add/", views.CreateDepotView.as_view(), name="add_depot"),
    path("depots/<int:pk>/edit/", views.UpdateDepotView.as_view(), name="edit_depot"),
    path("depots/delete/", views.DeleteDepotView.as_view(), name="delete_depot"),
    path(
        "depots/<int:pk>/set-active/",
        views.SetActiveDepotView.as_view(),
        name="set_depot",
    ),
    # alternative
    path(
        "alternatives/add/",
        views.CreateAlternativeView.as_view(),
        name="add_alternative",
    ),
    path(
        "alternatives/<int:pk>/edit/",
        views.UpdateAlternativeView.as_view(),
        name="edit_alternative",
    ),
    path(
        "alternatives/delete/",
        views.DeleteAlternativeView.as_view(),
        name="delete_alternative",
    ),
    # value
    path("values/add/", views.CreateValueView.as_view(), name="add_value"),
    path("values/<int:pk>/edit/", views.UpdateValueView.as_view(), name="edit_value"),
    path(
        "values/<int:pk>/delete/", views.DeleteValueView.as_view(), name="delete_value"
    ),
    # flow
    path("flows/add/", views.CreateFlowView.as_view(), name="add_flow"),
    path("flows/<int:pk>/edit/", views.UpdateFlowView.as_view(), name="edit_flow"),
    path("flows/<int:pk>/delete/", views.DeleteFlowView.as_view(), name="delete_flow"),
    # pages
    path("depots/<int:pk>/", views.DetailDepotView.as_view(), name="index"),
    path(
        "alternatives/<int:pk>/",
        views.DetailAlternativeView.as_view(),
        name="alternative",
    ),
]
