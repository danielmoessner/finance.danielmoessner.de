from django.urls import path

from apps.alternative import formviews, views

app_name = "alternative"

urlpatterns = [
    # depot
    path("depots/add/", formviews.CreateDepotView.as_view(), name="add_depot"),
    path(
        "depots/<int:pk>/edit/", formviews.UpdateDepotView.as_view(), name="edit_depot"
    ),
    path(
        "depots/<int:pk>/reset/", formviews.ResetDepotView.as_view(), name="reset_depot"
    ),
    path("depots/delete/", formviews.DeleteDepotView.as_view(), name="delete_depot"),
    path(
        "depots/<int:pk>/set-active/",
        formviews.SetActiveDepotView.as_view(),
        name="set_depot",
    ),
    # alternative
    path(
        "alternatives/add/",
        formviews.CreateAlternativeView.as_view(),
        name="add_alternative",
    ),
    path(
        "alternatives/<int:pk>/edit/",
        formviews.UpdateAlternativeView.as_view(),
        name="edit_alternative",
    ),
    path(
        "alternatives/delete/",
        formviews.DeleteAlternativeView.as_view(),
        name="delete_alternative",
    ),
    # value
    path("values/add/", formviews.CreateValueView.as_view(), name="add_value"),
    path(
        "values/<int:pk>/edit/", formviews.UpdateValueView.as_view(), name="edit_value"
    ),
    path(
        "values/<int:pk>/delete/",
        formviews.DeleteValueView.as_view(),
        name="delete_value",
    ),
    # flow
    path("flows/add/", formviews.CreateFlowView.as_view(), name="add_flow"),
    path("flows/<int:pk>/edit/", formviews.UpdateFlowView.as_view(), name="edit_flow"),
    path(
        "flows/<int:pk>/delete/", formviews.DeleteFlowView.as_view(), name="delete_flow"
    ),
    # pages
    path("depot/", views.DetailDepotView.as_view(), name="index"),
    path(
        "alternatives/<int:pk>/",
        views.DetailAlternativeView.as_view(),
        name="alternative",
    ),
]
