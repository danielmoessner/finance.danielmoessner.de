from django.urls import path

from apps.crypto import formviews, views

app_name = "crypto"

urlpatterns = [
    # depot
    path("depots/add/", formviews.AddDepotView.as_view(), name="add_depot"),
    path("depots/delete/", formviews.DeleteDepotView.as_view(), name="delete_depot"),
    path("depots/<int:pk>/edit/", formviews.EditDepotView.as_view(), name="edit_depot"),
    path(
        "depots/<int:pk>/set-active/",
        formviews.SetActiveDepotView.as_view(),
        name="set_depot",
    ),
    path("depots/<int:pk>/reset/", views.reset_depot_stats, name="reset_stats"),
    # account
    path("accounts/add/", formviews.AddAccountView.as_view(), name="add_account"),
    path(
        "accounts/delete/", formviews.DeleteAccountView.as_view(), name="delete_account"
    ),
    path(
        "accounts/<int:pk>/edit/",
        formviews.EditAccountView.as_view(),
        name="edit_account",
    ),
    # asset
    path("assets/add/", formviews.AddAssetView.as_view(), name="add_asset"),
    path("assets/<int:pk>/edit/", formviews.EditAssetView.as_view(), name="edit_asset"),
    path("assets/delete/", formviews.DeleteAssetView.as_view(), name="remove_asset"),
    # trade
    path("trades/add/", formviews.AddTradeView.as_view(), name="add_trade"),
    path("trades/<int:pk>/edit/", formviews.EditTradeView.as_view(), name="edit_trade"),
    path(
        "trades/<int:pk>/delete/",
        formviews.DeleteTradeView.as_view(),
        name="delete_trade",
    ),
    # transaction
    path(
        "transactions/add/",
        formviews.AddTransactionView.as_view(),
        name="add_transaction",
    ),
    path(
        "transactions/<int:pk>/edit/",
        formviews.EditTransactionView.as_view(),
        name="edit_transaction",
    ),
    path(
        "transactions/<int:pk>/delete/",
        formviews.DeleteTransactionView.as_view(),
        name="delete_transaction",
    ),
    # flows
    path("flows/add/", formviews.AddFlowView.as_view(), name="add_flow"),
    path("flows/<int:pk>/edit/", formviews.EditFlowView.as_view(), name="edit_flow"),
    path(
        "flows/<int:pk>/delete/", formviews.DeleteFlowView.as_view(), name="delete_flow"
    ),
    # price
    path("price/<int:pk>/edit/", formviews.EditPriceView.as_view(), name="edit_price"),
    path(
        "price/<int:pk>/delete/",
        formviews.DeletePriceView.as_view(),
        name="delete_price",
    ),
    # price fetcher
    path(
        "price-fetcher/add/",
        formviews.AddPriceFetcherView.as_view(),
        name="add_price_fetcher",
    ),
    path(
        "price-fetcher/<int:pk>/edit/",
        formviews.EditPriceFetcherView.as_view(),
        name="edit_price_fetcher",
    ),
    path(
        "price-fetcher/<int:pk>/delete/",
        formviews.DeletePriceFetcherView.as_view(),
        name="delete_price_fetcher",
    ),
    path(
        "price-fetcher/<int:pk>/run/",
        formviews.RunPriceFetcherView.as_view(),
        name="run_price_fetcher",
    ),
    # views
    path("depot/", views.IndexView.as_view(), name="index"),
    path("accounts/<int:pk>/", views.AccountView.as_view(), name="account"),
    path("assets/<int:pk>/", views.AssetView.as_view(), name="asset"),
]
