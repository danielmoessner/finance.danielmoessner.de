from django.contrib.auth.decorators import login_required
from django.conf.urls import url

from finance.banking.views import views
from finance.banking.views import form_views


app_name = "banking"


urlpatterns = [
    # API DATA
    # api-data/index/
    url(r"^api-data/index/$", login_required(views.IndexData.as_view()), name="api_data_index"),
    # api-data/account/comdirect/
    url(r"^api-data/account/(?P<slug>[0-9a-zA-Z-#]*)/$", login_required(
        views.AccountData.as_view()),
        name="api_data_account"),
    # api-data/categories/
    url(r"^api-data/categories/$", login_required(views.CategoriesData.as_view()),
        name="api_data_categories"),
    # api-data/category/enjoyment/
    url(r"^api-data/category/(?P<slug>[0-9a-zA-Z-#]*)/$", login_required(
        views.CategoryData.as_view()), name="api_data_category"),

    # FUNCTIONS
    # update-movies/
    url(r"^update-movies", login_required(views.update_movies), name="update_stats"),

    # account
    url(r"^add-account/$",
        login_required(form_views.AddAccountView.as_view()),
        name="add_account"),
    url(r"^edit-account/(?P<slug>[0-9a-zA-Z-#]*)/$",
        login_required(form_views.EditAccountView.as_view()),
        name="edit_account"),
    url(r"^delete-account/$",
        login_required(form_views.DeleteAccountView.as_view()),
        name="delete_account"),

    # category
    url(r"^add-category/$",
        login_required(form_views.AddCategoryView.as_view()),
        name="add_category"),
    url(r"^edit-category/(?P<slug>[0-9a-zA-Z-#]*)/$",
        login_required(form_views.EditCategoryView.as_view()),
        name="edit_category"),
    url(r"^delete-category/$",
        login_required(form_views.DeleteCategoryView.as_view()),
        name="delete_category"),

    # change
    url(r"^add-change/$",
        login_required(form_views.AddChangeIndexView.as_view()),
        name="add_change"),
    url(r"^account/(?P<slug>[0-9a-zA-Z-#]*)/add-change/$",
        login_required(form_views.AddChangeAccountView.as_view()),
        name="add_change"),
    url(r"^account/(?P<slug>[0-9a-zA-Z-#]*)/edit-change/(?P<pk>\d+)/$",
        login_required(form_views.EditChangeView.as_view()),
        name="edit_change"),
    url(r"^account/(?P<slug>[0-9a-zA-Z-#]*)/delete-change/(?P<pk>\d+)/$",
        login_required(form_views.DeleteChangeView.as_view()),
        name="delete_change"),

    # timespan
    url(r"^add-timespan/$",
        login_required(form_views.AddTimespanView.as_view()),
        name="add_timespan"),
    url(r"^delete-timespan/(?P<pk>\d+)/$",
        login_required(form_views.DeleteTimespanView.as_view()),
        name="delete_timespan"),
    url(r"^set-timespan/(?P<pk>\d+)/$",
        login_required(form_views.SetActiveTimespanView.as_view()),
        name="set_timespan"),

    # PAGES
    # index
    url(r"^$", login_required(views.IndexView.as_view()), name="index"),
    # account/comdirect/
    url(r"^account/(?P<slug>[0-9a-zA-Z-#]*)/$", login_required(views.AccountView.as_view()),
        name="account"),
    # category/food/
    url(r"^category/(?P<slug>[0-9a-zA-Z-#]*)/$", login_required(views.CategoryView.as_view()),
        name="category"),
]
