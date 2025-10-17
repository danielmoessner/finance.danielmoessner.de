from django.urls import path

from apps.banking import api, formviews, views

app_name = "banking"


urlpatterns = [
    # charts
    path(
        "api/depots/<int:pk>/income-and-expenditure-data/",
        api.IncomeAndExpenditureData.as_view(),
        name="api_depot_income_and_expenditure_data",
    ),
    path(
        "api/depots/<int:pk>/balance-data/",
        api.BalanceData.as_view(),
        name="api_depot_balance_data",
    ),
    # depots
    path("depots/add/", formviews.AddDepotView.as_view(), name="add_depot"),
    path("depots/delete/", formviews.DeleteDepotView.as_view(), name="delete_depot"),
    path("depots/<int:pk>/edit/", formviews.EditDepotView.as_view(), name="edit_depot"),
    path(
        "depots/<int:pk>/set-active/",
        formviews.SetActiveDepotView.as_view(),
        name="set_depot",
    ),
    # accounts
    path("accounts/add/", formviews.AddAccountView.as_view(), name="add_account"),
    path(
        "accounts/delete/", formviews.DeleteAccountView.as_view(), name="delete_account"
    ),
    path(
        "accounts/<int:pk>/edit/",
        formviews.EditAccountView.as_view(),
        name="edit_account",
    ),
    # categories
    path("categories/add/", formviews.AddCategoryView.as_view(), name="add_category"),
    path(
        "categories/delete/",
        formviews.DeleteCategoryView.as_view(),
        name="delete_category",
    ),
    path(
        "categories/<int:pk>/edit/",
        formviews.EditCategoryView.as_view(),
        name="edit_category",
    ),
    # changes
    path("changes/add/", formviews.AddChangeView.as_view(), name="add_change"),
    path(
        "changes/<int:pk>/edit/", formviews.EditChangeView.as_view(), name="edit_change"
    ),
    path(
        "changes/<int:pk>/delete/",
        formviews.DeleteChangeView.as_view(),
        name="delete_change",
    ),
    path(
        "changes/money-move/",
        formviews.MoneyMoveView.as_view(),
        name="move_money",
    ),
    path("changes/import/", formviews.ImportView.as_view(), name="import_changes"),
    path(
        "changes/import/comdirect/<int:pk>/run/",
        formviews.ComdirectStartLoginView.as_view(),
        name="run_comdirect_import",
    ),
    path(
        "changes/import/comdirect/change/<int:pk>/",
        formviews.ComdirectImportChangeView.as_view(),
        name="import_comdirect_change",
    ),
    path(
        "changes/import/comdirect/change/<int:pk>/delete/",
        formviews.DeleteComdirectChangeView.as_view(),
        name="delete_comdirect_change",
    ),
    # pages
    path("depot/", views.IndexView.as_view(), name="index"),
    path("accounts/<int:pk>/", views.AccountView.as_view(), name="account"),
    path("categories/<int:pk>/", views.CategoryView.as_view(), name="category"),
    # frontend
    path("store/<str:key>/<str:value>/", views.store, name="store"),
]
