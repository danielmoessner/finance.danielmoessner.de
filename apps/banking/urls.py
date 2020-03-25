from rest_framework import routers
from django.urls import path, include

from apps.banking import formviews
from apps.banking import views
from apps.banking import api

app_name = "banking"

router = routers.DefaultRouter()
router.register(r'categories', api.CategoryViewSet)
router.register(r'accounts', api.AccountViewSet)
router.register(r'changes', api.ChangeViewSet)
router.register(r'depots', api.DepotViewSet)

urlpatterns = [
    # api
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # charts
    path('api/depots/<int:pk>/income-and-expenditure-data/', api.IncomeAndExpenditureData.as_view(),
         name='api_depot_income_and_expenditure_data'),
    path('api/depots/<int:pk>/balance-data/', api.BalanceData.as_view(), name='api_depot_balance_data'),

    # depots
    path("depots/add/", formviews.AddDepotView.as_view(), name="add_depot"),
    path("depots/delete/", formviews.DeleteDepotView.as_view(), name="delete_depot"),
    path("depots/<int:pk>/edit/", formviews.EditDepotView.as_view(), name="edit_depot"),
    path("depots/<int:pk>/set-active/", formviews.SetActiveDepotView.as_view(), name="set_depot"),

    # accounts
    path("accounts/add/", formviews.AddAccountView.as_view(), name="add_account"),
    path("accounts/delete/", formviews.DeleteAccountView.as_view(), name="delete_account"),
    path("accounts/<int:pk>/edit/", formviews.EditAccountView.as_view(), name="edit_account"),

    # categories
    path("categories/add/", formviews.AddCategoryView.as_view(), name="add_category"),
    path("categories/delete/", formviews.DeleteCategoryView.as_view(), name="delete_category"),
    path("categories/<int:pk>/edit/", formviews.EditCategoryView.as_view(), name="edit_category"),

    # changes
    path("changes/add/", formviews.AddChangeView.as_view(), name="add_change"),
    path("changes/<int:pk>/edit/", formviews.EditChangeView.as_view(), name="edit_change"),
    path("changes/<int:pk>/delete/", formviews.DeleteChangeView.as_view(), name="delete_change"),

    # pages
    path("depots/<int:pk>/", views.IndexView.as_view(), name="index"),
    path("accounts/<int:pk>/", views.AccountView.as_view(), name="account"),
    path("categories/<int:pk>/", views.CategoryView.as_view(), name="category"),
]
