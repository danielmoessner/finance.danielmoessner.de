from django.contrib.auth.decorators import login_required
from django.conf.urls import url
from finance.alternative.views import views
from finance.alternative.views import form_views


app_name = "alternative"


urlpatterns = [
    # API DATA
    # url(r"^api-data/index/$", login_required(views.IndexData.as_view()),
    #     name="api_data_index"),
    # url(r"^api-data/categories/$", login_required(views.CategoriesData.as_view()),
    #     name="api_data_categories"),
    # url(r"^api-data/categories-month/$", login_required(views.CategoriesMonthData.as_view()),
    #     name="api_data_categories_month"),
    # url(r"^api-data/account/(?P<slug>[0-9a-zA-Z-#]*)/$", login_required(views.AccountData.as_view()),
    #     name="api_data_account"),
    # url(r"^api-data/category/(?P<slug>[0-9a-zA-Z-#]*)/$", login_required(views.CategoryData.as_view()),
    #     name="api_data_category"),

    # FUNCTIONS
    # update-movies/
    # url(r"^update-movies", login_required(views.update_movies), name="update_movies"),
    # # reset-movies/
    # url(r"^reset-movies", login_required(views.reset_movies), name="reset_movies"),

    # depot
    url(r"^add-depot/$",
        login_required(form_views.AddDepotView.as_view()),
        name="add_depot"),
    url(r"^edit-depot/(?P<pk>\d+)/$",
        login_required(form_views.EditDepotView.as_view()),
        name="edit_depot"),
    url(r"^delete-depot/$",
        login_required(form_views.DeleteDepotView.as_view()),
        name="delete_depot"),
    url(r"^set-depot/(?P<pk>\d+)/$",
        login_required(form_views.SetActiveDepotView.as_view()),
        name="set_depot"),

    # alternative
    url(r"^add-alternative/$",
        login_required(form_views.AddAlternativeView.as_view()),
        name="add_alternative"),
    url(r"^edit-alternative/(?P<slug>[0-9a-zA-Z-#]*)/$",
        login_required(form_views.EditAlternativeView.as_view()),
        name="edit_alternative"),
    url(r"^delete-alternative/$",
        login_required(form_views.DeleteAlternativeView.as_view()),
        name="delete_alternative"),

    # value
    url(r"^add-value/$",
        login_required(form_views.AddValueView.as_view()),
        name="add_value"),
    url(r"^alternative/(?P<slug>[0-9a-zA-Z-#]*)/add-value/$",
        login_required(form_views.AddValueAlternativeView.as_view()),
        name="add_value"),
    url(r"^alternative/(?P<slug>[0-9a-zA-Z-#]*)/edit-value/(?P<pk>\d+)/$",
        login_required(form_views.EditValueView.as_view()),
        name="edit_value"),
    url(r"^alternative/(?P<slug>[0-9a-zA-Z-#]*)/delete-value/(?P<pk>\d+)/$",
        login_required(form_views.DeleteValueView.as_view()),
        name="delete_value"),

    # flow
    url(r"^add-flow/$",
        login_required(form_views.AddFlowView.as_view()),
        name="add_flow"),
    url(r"^alternative/(?P<slug>[0-9a-zA-Z-#]*)/add-flow/$",
        login_required(form_views.AddFlowAlternativeView.as_view()),
        name="add_flow"),
    url(r"^alternative/(?P<slug>[0-9a-zA-Z-#]*)/edit-flow/(?P<pk>\d+)/$",
        login_required(form_views.EditFlowView.as_view()),
        name="edit_flow"),
    url(r"^alternative/(?P<slug>[0-9a-zA-Z-#]*)/delete-flow/(?P<pk>\d+)/$",
        login_required(form_views.DeleteFlowView.as_view()),
        name="delete_flow"),

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
    url(r"^$", login_required(views.IndexView.as_view()), name="index"),
    url(r"^alternative/(?P<slug>[0-9a-zA-Z-#]*)/$", login_required(views.AlternativeView.as_view()),
        name="alternative"),
]