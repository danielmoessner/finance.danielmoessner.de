from django.urls import path

from apps.stocks import views

app_name = "stocks"

urlpatterns = [
    # depot
    path("depots/add/", views.CreateDepotView.as_view(), name="add_depot"),
    path("depots/delete/", views.DeleteDepotView.as_view(), name="delete_depot"),
    path("depots/<int:pk>/edit/", views.EditDepotView.as_view(), name="edit_depot"),
    path("depots/<int:pk>/set-active/", views.SetActiveDepotView.as_view(), name="set_depot"),
    # path("depots/<int:pk>/reset/", views.reset_depot_stats, name="reset_stats"),

    # account
    path("accounts/add/", views.AddBankView.as_view(), name="add_bank"),
    path("accounts/delete/", views.DeleteBankView.as_view(), name="delete_bank"),
    path("accounts/<int:pk>/edit/", views.EditBankView.as_view(), name="edit_bank"),

    # asset
    path("stocks/add/", views.AddStockView.as_view(), name="add_stock"),
    path("stocks/<int:pk>/edit/", views.EditStockView.as_view(), name="edit_stock"),
    path("stocks/delete/", views.DeleteStockView.as_view(), name="delete_stock"),

    # # trade
    path("trades/add/", views.AddTradeView.as_view(), name="add_trade"),
    path("trades/<int:pk>/edit/", views.EditTradeView.as_view(), name="edit_trade"),
    path("trades/<int:pk>/delete/", views.DeleteTradeView.as_view(), name="delete_trade"),

    # flows
    path("flows/add/", views.AddFlowView.as_view(), name="add_flow"),
    path("flows/<int:pk>/edit/", views.EditFlowView.as_view(), name="edit_flow"),
    path("flows/<int:pk>/delete/", views.DeleteFlowView.as_view(), name="delete_flow"),

    # views
    path("depots/<int:pk>/", views.IndexView.as_view(), name="index"),
    path("banks/<int:pk>/", views.BankView.as_view(), name="banks"),
    path("stocks/<int:pk>/", views.StockView.as_view(), name="stocks"),
]
