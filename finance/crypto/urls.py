from django.contrib.auth.decorators import login_required
from django.conf.urls import url

from finance.crypto.views import views
from finance.crypto.views import form_views


app_name = "crypto"


urlpatterns = [
    # API DATA
    # api-data/index/
    url(r"^api/index/$", login_required(views.IndexData.as_view()), name="api_data_index"),
    # api-data/account/bittrex/
    url(r"^api/account/(?P<slug>[0-9a-zA-Z-#]*)/$", login_required(
        views.AccountData.as_view()), name="api_data_account"),
    # api-data/assets/
    url(r"^api/assets/$", login_required(views.AssetsData.as_view()), name="api_data_assets"),
    # api-data/asset/bitcoin/
    url(r"^api/asset/(?P<slug>[0-9a-zA-Z-#]*)/$", login_required(views.AssetData.as_view()),
        name="api_data_asset"),

    # FUNCTIONS
    # update-movies/
    url(r"^update-movies", login_required(views.update_movies), name="update_movies"),
    # reset-movies/
    url(r"^reset-movies", login_required(views.reset_movies), name="reset_movies"),

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

    # account
    url(r"^add-account/$",
        login_required(form_views.AddAccountView.as_view()),
        name="add_account"),
    url(r"^edit-account/(?P<slug>[0-9a-zA-Z-#]*)$",
        login_required(form_views.EditAccountView.as_view()),
        name="edit_account"),
    url(r"^delete-account/$",
        login_required(form_views.DeleteAccountView.as_view()),
        name="delete_account"),

    # asset
    url(r"^add-asset/$",
        login_required(form_views.AddAssetView.as_view()),
        name="add_asset"),
    url(r"^remove-asset/$",
        login_required(form_views.RemoveAssetView.as_view()),
        name="remove_asset"),

    # trade
    url(r"^add-trade/$",
        login_required(form_views.AddTradeView.as_view()),
        name="add_trade"),
    url(r"^account/(?P<slug>[0-9a-zA-Z-#]*)/add-trade/$",
        login_required(form_views.AddTradeAccountView.as_view()),
        name="add_trade"),
    url(r"^edit-trade/(?P<pk>\d+)/$",
        login_required(form_views.EditTradeView.as_view()),
        name="edit_trade"),
    url(r"^delete-trade/(?P<pk>\d+)/$",
        login_required(form_views.DeleteTradeView.as_view()),
        name="delete_trade"),

    # transaction
    url(r"^add-transaction/$",
        login_required(form_views.AddTransactionView.as_view()),
        name="add_transaction"),
    url(r"^edit-transaction/(?P<pk>\d+)/$",
        login_required(form_views.EditTransactionView.as_view()),
        name="edit_transaction"),
    url(r"^delete-transaction/(?P<pk>\d+)/$",
        login_required(form_views.DeleteTransactionView.as_view()),
        name="delete_transaction"),

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
    # account/bittrex/
    url(r"^account/(?P<slug>[0-9a-zA-Z-#]*)/$", login_required(views.AccountView.as_view()),
        name="account"),
    # asset/bitcoin/
    url(r"^asset/(?P<slug>[0-9a-zA-Z-#]*)/$", login_required(views.AssetView.as_view()),
        name="asset"),
]
