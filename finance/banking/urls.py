from django.contrib.auth.decorators import login_required
from django.conf.urls import url
from django.urls import path

from finance.banking.views import views
from finance.banking.views import form_views


app_name = "banking"


urlpatterns = [
    # API DATA
    path("api/index/", login_required(views.IndexData.as_view()), name="api_data_index"),
    path("api/categories/", login_required(views.CategoriesData.as_view()), name="api_data_categories"),
    path("api/categories-month/", login_required(views.CategoriesMonthData.as_view()),
         name="api_data_categories_month"),
    path("api/account/<slug>/", login_required(views.AccountData.as_view()), name="api_data_account"),
    path("api/category/<slug>/", login_required(views.CategoryData.as_view()), name="api_data_category"),

    # FUNCTIONS
    path("update-movies", login_required(views.update_movies), name="update_movies"),
    path("reset-movies", login_required(views.reset_movies), name="reset_movies"),

    # depot
    path("depot/add", login_required(form_views.AddDepotView.as_view()), name="add_depot"),
    path("depot/delete/", login_required(form_views.DeleteDepotView.as_view()), name="delete_depot"),
    path("depot/<pk>/edit/", login_required(form_views.EditDepotView.as_view()), name="edit_depot"),
    path("depot/<pk>/set", login_required(form_views.SetActiveDepotView.as_view()), name="set_depot"),

    # account
    path("account/add/", login_required(form_views.AddAccountView.as_view()), name="add_account"),
    path("account/delete", login_required(form_views.DeleteAccountView.as_view()), name="delete_account"),
    path("account/<slug>/edit/", login_required(form_views.EditAccountView.as_view()), name="edit_account"),

    # category
    path("category/add/", login_required(form_views.AddCategoryView.as_view()), name="add_category"),
    path("category/delete/", login_required(form_views.DeleteCategoryView.as_view()), name="delete_category"),
    path("category/<slug>/edit/", login_required(form_views.EditCategoryView.as_view()), name="edit_category"),

    # change
    path("change/add/", login_required(form_views.AddChangeIndexView.as_view()), name="add_change"),
    path("account/<slug>/change/add/", login_required(form_views.AddChangeAccountView.as_view()), name="add_change"),
    path("account/<slug>/change/<pk>/edit/", login_required(form_views.EditChangeView.as_view()), name="edit_change"),
    path("account/<slug>/change/<pk>/delete/", login_required(form_views.DeleteChangeView.as_view()),
         name="delete_change"),

    # timespan
    path("timespan/add/", login_required(form_views.AddTimespanView.as_view()), name="add_timespan"),
    path("timespan/<pk>/delete", login_required(form_views.DeleteTimespanView.as_view()), name="delete_timespan"),
    path("timespan/<pk>/set", login_required(form_views.SetActiveTimespanView.as_view()), name="set_timespan"),

    # PAGES
    path("", login_required(views.IndexView.as_view()), name="index"),
    path("account/<slug>/", login_required(views.AccountView.as_view()), name="account"),
    path("category/<slug>/", login_required(views.CategoryView.as_view()), name="category"),
]
