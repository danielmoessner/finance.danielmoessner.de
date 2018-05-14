from django.contrib.auth.decorators import login_required
from django.conf.urls import url

from . import views


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
    # update-stats/
    url(r"^update-stats", login_required(views.update_stats), name="update_stats"),

    # add-account/
    url(r"^add-account/$", login_required(views.add), name="add_account"),
    # edit-account/
    url(r"^edit-account/$", login_required(views.edit), name="edit_account"),
    # delete-account/
    url(r"^delete-account/$", login_required(views.delete), name="delete_account"),

    # add-category/
    url(r"^add-category/$", login_required(views.add), name="add_category"),
    # edit-category/
    url(r"^edit-category/$", login_required(views.edit), name="edit_category"),
    # delete-category/
    url(r"^delete-category/$", login_required(views.delete), name="delete_category"),

    # add-change/
    url(r"^add-change/$", login_required(views.add), name="add_change"),
    # edit-change/
    url(r"^edit-change/$", login_required(views.edit), name="edit_change"),
    # delete-change/
    url(r"^delete-change/$", login_required(views.delete), name="delete_change"),

    # add-timespan/
    url(r"^add-timespan/$", login_required(views.add), name="add_timespan"),
    # delete-timespan/
    url(r"^delete-timespan/$", login_required(views.delete), name="delete_timespan"),
    # set-timespan/
    url(r"^set-timespan/$", login_required(views.set_timespan), name="set_timespan"),
    # update-timespans/
    url(r"^update-timespans/$", login_required(views.update_timespans), name="update_timespans"),

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
