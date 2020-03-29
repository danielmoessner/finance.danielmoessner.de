from django.urls import path

from apps.crypto.views import views
from apps.crypto.views import form_views


app_name = "crypto"


urlpatterns = [
    # API DATA
    # api-data/index/
    path("api/index/", views.IndexData.as_view(), name="api_data_index"),
    # api-data/account/bittrex/
    path("api/account/<slug>/",  views.AccountData.as_view(), name="api_data_account"),
    # api-data/assets/
    path("api/assets/", views.AssetsData.as_view(), name="api_data_assets"),
    # api-data/asset/bitcoin/
    path("api/asset/<slug>/", views.AssetData.as_view(), name="api_data_asset"),

    # FUNCTIONS
    # update-movies/
    path("update-movies/", views.update_movies, name="update_movies"),
    # reset-movies/
    path("reset-movies/", views.reset_movies, name="reset_movies"),

    # depot
    path("depot/add/", form_views.AddDepotView.as_view(), name="add_depot"),
    path("depot/delete/", form_views.DeleteDepotView.as_view(), name="delete_depot"),
    path("depot/<pk>/edit/", form_views.EditDepotView.as_view(), name="edit_depot"),
    path("depot/<pk>/set-active/", form_views.SetActiveDepotView.as_view(), name="set_depot"),

    # account
    path("account/add/", form_views.AddAccountView.as_view(), name="add_account"),
    path("account/delete/", form_views.DeleteAccountView.as_view(), name="delete_account"),
    path("account/<slug>/edit/", form_views.EditAccountView.as_view(), name="edit_account"),

    # asset
    path("asset/add/", form_views.AddAssetView.as_view(), name="add_asset"),
    path("asset/remove/", form_views.RemoveAssetView.as_view(), name="remove_asset"),

    # trade
    path("trade/add/", form_views.AddTradeView.as_view(), name="add_trade"),
    path("account/<slug>/trade/add/", form_views.AddTradeAccountView.as_view(), name="add_trade"),
    path("trade/<pk>/edit/", form_views.EditTradeView.as_view(), name="edit_trade"),
    path("trade/<pk>/delete/", form_views.DeleteTradeView.as_view(), name="delete_trade"),

    # transaction
    path("transaction/add/", form_views.AddTransactionView.as_view(), name="add_transaction"),
    path("transaction/<pk>/edit/", form_views.EditTransactionView.as_view(), name="edit_transaction"),
    path("transaction/<pk>/delete/", form_views.DeleteTransactionView.as_view(), name="delete_transaction"),

    # timespan
    path("timespan/add/", form_views.AddTimespanView.as_view(), name="add_timespan"),
    path("timespan/<pk>/delete/", form_views.DeleteTimespanView.as_view(), name="delete_timespan"),
    path("timespan/<pk>/set/", form_views.SetActiveTimespanView.as_view(), name="set_timespan"),

    # PAGES
    # index
    path("depots/<int:pk>/", views.IndexView.as_view(), name="index"),
    # account/bittrex/
    path("account/<slug>/", views.AccountView.as_view(), name="account"),
    # asset/bitcoin/
    path("asset/<slug>/", views.AssetView.as_view(), name="asset"),
]
