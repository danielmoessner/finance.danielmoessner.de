from rest_framework import routers
from django.urls import path, include

from apps.banking.views import form_views
from apps.banking.views import views
from apps.banking.views import api

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
    path('api/depots/<int:pk>/income-and-expenditure-data/', views.IncomeAndExpenditureData.as_view(),
         name='api_depot_income_and_expenditure_data'),
    path('api/depots/<int:pk>/balance-data/', views.BalanceData.as_view(), name='api_depot_balance_data'),

    # functions
    path("reset-balances/", views.reset_balances, name="reset_balances"),

    # depots
    path("depots/add/", form_views.AddDepotView.as_view(), name="add_depot"),
    path("depots/delete/", form_views.DeleteDepotView.as_view(), name="delete_depot"),
    path("depots/<int:pk>/edit/", form_views.EditDepotView.as_view(), name="edit_depot"),
    path("depots/<int:pk>/set-active/", form_views.SetActiveDepotView.as_view(), name="set_depot"),

    # accounts
    path("accounts/add/", form_views.AddAccountView.as_view(), name="add_account"),
    path("accounts/delete/", form_views.DeleteAccountView.as_view(), name="delete_account"),
    path("accounts/<int:pk>/edit/", form_views.EditAccountView.as_view(), name="edit_account"),

    # categories
    path("categories/add/", form_views.AddCategoryView.as_view(), name="add_category"),
    path("categories/delete/", form_views.DeleteCategoryView.as_view(), name="delete_category"),
    path("categories/<int:pk>/edit/", form_views.EditCategoryView.as_view(), name="edit_category"),

    # changes
    path("changes/add/", form_views.AddChangeView.as_view(), name="add_change"),
    path("changes/<int:pk>/edit/", form_views.EditChangeView.as_view(), name="edit_change"),
    path("changes/<int:pk>/delete/", form_views.DeleteChangeView.as_view(), name="delete_change"),

    # pages
    path("depots/<int:pk>/", views.IndexView.as_view(), name="index"),
    path("accounts/<int:pk>/", views.AccountView.as_view(), name="account"),
    path("categories/<int:pk>/", views.CategoryView.as_view(), name="category"),
]
