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
    # API
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # API DATA
    # path("api/index/", views.IndexData.as_view(), name="api_data_index"),
    # path("api/categories/", views.CategoriesData.as_view(), name="api_data_categories"),
    # path("api/categories-month/", views.CategoriesMonthData.as_view(), name="api_data_categories_month"),
    # path("api/account/<slug>/", views.AccountData.as_view(), name="api_data_account"),
    # path("api/category/<slug>/", views.CategoryData.as_view(), name="api_data_category"),

    # FUNCTIONS
    path("reset-balances", views.reset_balances, name="reset_balances"),

    # depot
    path("depot/add", form_views.AddDepotView.as_view(), name="add_depot"),
    path("depot/delete/", form_views.DeleteDepotView.as_view(), name="delete_depot"),
    path("depot/<pk>/edit/", form_views.EditDepotView.as_view(), name="edit_depot"),
    path("depot/<pk>/set", form_views.SetActiveDepotView.as_view(), name="set_depot"),

    # account
    path("account/add/", form_views.AddAccountView.as_view(), name="add_account"),
    path("account/delete", form_views.DeleteAccountView.as_view(), name="delete_account"),
    path("account/<slug>/edit/", form_views.EditAccountView.as_view(), name="edit_account"),

    # category
    path("category/add/", form_views.AddCategoryView.as_view(), name="add_category"),
    path("category/delete/", form_views.DeleteCategoryView.as_view(), name="delete_category"),
    path("category/<slug>/edit/", form_views.EditCategoryView.as_view(), name="edit_category"),

    # change
    path("change/add/", form_views.AddChangeIndexView.as_view(), name="add_change"),
    path("account/<slug>/change/add/", form_views.AddChangeAccountView.as_view(), name="add_change"),
    path("account/<slug>/change/<pk>/edit/", form_views.EditChangeView.as_view(), name="edit_change"),
    path("account/<slug>/change/<pk>/delete/", form_views.DeleteChangeView.as_view(), name="delete_change"),

    # timespan
    path("timespan/add/", form_views.AddTimespanView.as_view(), name="add_timespan"),
    path("timespan/<pk>/delete", form_views.DeleteTimespanView.as_view(), name="delete_timespan"),
    path("timespan/<pk>/set", form_views.SetActiveTimespanView.as_view(), name="set_timespan"),

    # PAGES
    path("depot/<int:pk>/", views.IndexView.as_view(), name="index"),
    path("account/<slug>/", views.AccountView.as_view(), name="account"),
    path("category/<slug>/", views.CategoryView.as_view(), name="category"),
]
