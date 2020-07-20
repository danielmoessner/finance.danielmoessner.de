from django.urls import path

from apps.stocks import views

app_name = "stocks"

urlpatterns = [
    # # depot
    path("depots/add/", views.CreateDepotView.as_view(), name="add_depot"),
    path("depots/delete/", views.DeleteDepotView.as_view(), name="delete_depot"),
    path("depots/<int:pk>/edit/", views.EditDepotView.as_view(), name="edit_depot"),
    path("depots/<int:pk>/set-active/", views.SetActiveDepotView.as_view(), name="set_depot"),
    # path("depots/<int:pk>/reset/", views.reset_depot_stats, name="reset_stats"),
    #
    # # account
    # path("accounts/add/", formviews.AddAccountView.as_view(), name="add_account"),
    # path("accounts/delete/", formviews.DeleteAccountView.as_view(), name="delete_account"),
    # path("accounts/<int:pk>/edit/", formviews.EditAccountView.as_view(), name="edit_account"),
    #
    # # asset
    # path("stocks/add/", formviews.AddStockView.as_view(), name="add_stock"),
    # path("stocks/<int:pk>/edit/", formviews.EditStockView.as_view(), name="edit_stock"),
    # path("stocks/delete/", formviews.DeleteStockView.as_view(), name="delete_stock"),
    #
    # # trade
    # path("trades/add/", formviews.AddTradeView.as_view(), name="add_trade"),
    # path("trades/<int:pk>/edit/", formviews.EditTradeView.as_view(), name="edit_trade"),
    # path("trades/<int:pk>/delete/", formviews.DeleteTradeView.as_view(), name="delete_trade"),
    #
    # # flows
    # path("flows/add/", formviews.AddFlowView.as_view(), name="add_flow"),
    # path("flows/<int:pk>/edit/", formviews.EditFlowView.as_view(), name="edit_flow"),
    # path("flows/<int:pk>/delete/", formviews.DeleteFlowView.as_view(), name="delete_flow"),

    # views
    path("depots/<int:pk>/", views.IndexView.as_view(), name="index"),
    path("banks/<int:pk>/", views.BankView.as_view(), name="banks"),
    path("stocks/<int:pk>/", views.StockView.as_view(), name="stocks"),
]
