from django.urls import path

from apps.crypto.views import views
from apps.crypto.views import form_views

app_name = "crypto"

urlpatterns = [
    # functions
    path("update-movies/", views.update_movies, name="update_movies"),
    path("reset-movies/", views.reset_movies, name="reset_movies"),

    # depot
    path("depots/add/", form_views.AddDepotView.as_view(), name="add_depot"),
    path("depots/delete/", form_views.DeleteDepotView.as_view(), name="delete_depot"),
    path("depots/<int:pk>/edit/", form_views.EditDepotView.as_view(), name="edit_depot"),
    path("depots/<int:pk>/set-active/", form_views.SetActiveDepotView.as_view(), name="set_depot"),

    # account
    path("accounts/add/", form_views.AddAccountView.as_view(), name="add_account"),
    path("accounts/delete/", form_views.DeleteAccountView.as_view(), name="delete_account"),
    path("accounts/<int:pk>/edit/", form_views.EditAccountView.as_view(), name="edit_account"),

    # asset
    path("assets/add/", form_views.AddAssetView.as_view(), name="add_asset"),
    path("assets/remove/", form_views.RemoveAssetView.as_view(), name="remove_asset"),

    # trade
    path("trades/add/", form_views.AddTradeView.as_view(), name="add_trade"),
    path("trades/<int:pk>/edit/", form_views.EditTradeView.as_view(), name="edit_trade"),
    path("trades/<int:pk>/delete/", form_views.DeleteTradeView.as_view(), name="delete_trade"),

    # transaction
    path("transactions/add/", form_views.AddTransactionView.as_view(), name="add_transaction"),
    path("transactions/<int:pk>/edit/", form_views.EditTransactionView.as_view(), name="edit_transaction"),
    path("transactions/<int:pk>/delete/", form_views.DeleteTransactionView.as_view(), name="delete_transaction"),

    # timespan
    path("timespans/add/", form_views.AddTimespanView.as_view(), name="add_timespan"),
    path("timespans/<int:pk>/delete/", form_views.DeleteTimespanView.as_view(), name="delete_timespan"),
    path("timespans/<int:pk>/set/", form_views.SetActiveTimespanView.as_view(), name="set_timespan"),

    # views
    path("depots/<int:pk>/", views.IndexView.as_view(), name="index"),
    path("accounts/<int:pk>/", views.AccountView.as_view(), name="account"),
    path("assets/<int:pk>/", views.AssetView.as_view(), name="asset"),
]
