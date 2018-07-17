from django.contrib.auth.decorators import login_required
from django.conf.urls import url

from finance.crypto.views import views
from finance.crypto.views import form_views


app_name = "crypto"


urlpatterns = [
    # API DATA
    # api-data/index/
    url(r"^api-data/index/$", login_required(views.IndexData.as_view()), name="api_data_index"),
    # api-data/account/bittrex/
    url(r"^api-data/account/(?P<slug>[0-9a-zA-Z-#]*)/$", login_required(
        views.AccountData.as_view()), name="api_data_account"),
    # api-data/assets/
    url(r"^api-data/assets/$", login_required(views.AssetsData.as_view()), name="api_data_assets"),
    # api-data/asset/bitcoin/
    url(r"^api-data/asset/(?P<slug>[0-9a-zA-Z-#]*)/$", login_required(views.AssetData.as_view()),
        name="api_data_asset"),

    # FUNCTIONS
    # update-movie/
    url(r"^update-movies", login_required(views.update_movies), name="update_movies"),

    # asset/bitcoin/add-price/
    url(r"^asset/(?P<slug>[0-9a-zA-Z-#]*)/add-price/$",
        login_required(form_views.AssetCreatePriceView.as_view()),
        name="add_price"),
    # asset/bitcoin/delete-price/
    url(r"^asset/(?P<slug>[0-9a-zA-Z-#]*)/delete-price/$",
        login_required(form_views.AssetDeletePriceView.as_view()),
        name="delete_price"),

    # add-account/
    url(r"^add-account/$",
        login_required(form_views.IndexCreateAccountView.as_view()),
        name="add_account"),
    # edit-account/
    url(r"^edit-account/$",
        login_required(form_views.IndexUpdateAccountView.as_view()),
        name="edit_account"),
    # delete-account/
    url(r"^delete-account/$",
        login_required(form_views.IndexDeleteAccountView.as_view()),
        name="delete_account"),

    # add-asset/
    url(r"^add-asset/$",
        login_required(form_views.IndexConnectDepotAssetView.as_view()),
        name="add_asset"),
    # add-private-asset/
    url(r"^add-private-asset/$",
        login_required(form_views.IndexCreatePrivateAssetView.as_view()),
        name="add_private_asset"),
    # edit-private-asset/
    url(r"^edit-private-asset/$",
        login_required(form_views.IndexUpdatePrivateAssetView.as_view()),
        name="edit_private_asset"),
    # delete-asset/
    url(r"^remove-asset/$",
        login_required(form_views.IndexRemoveAssetView.as_view()),
        name="remove_asset"),
    # delete-private-asset/
    url(r"^delete-private-asset/$",
        login_required(form_views.IndexDeletePrivateAssetView.as_view()),
        name="delete_private_asset"),

    # add-trade/
    url(r"^add-trade/$",
        login_required(form_views.IndexCreateTradeView.as_view()),
        name="add_trade"),
    # account/bittrex/add-trade/
    url(r"^account/(?P<slug>[0-9a-zA-Z-#]*)/add-trade/$",
        login_required(form_views.AccountCreateTradeView.as_view()),
        name="add_trade"),
    # account/bittrex/edit-trade/
    url(r"^account/(?P<slug>[0-9a-zA-Z-#]*)/edit-trade/$",
        login_required(form_views.AccountUpdateTradeView.as_view()),
        name="edit_trade"),
    # account/bittrex/delete-trade/
    url(r"^account/(?P<slug>[0-9a-zA-Z-#]*)/delete-trade/$",
        login_required(form_views.AccountDeleteTradeView.as_view()),
        name="delete_trade"),

    # account/bittrex/add-transaction/
    url(r"^account/(?P<slug>[0-9a-zA-Z-#]*)/add-transaction/$",
        login_required(form_views.AccountCreateTransactionView.as_view()),
        name="add_transaction"),
    # account/bittrex/edit-transaction/
    url(r"^account/(?P<slug>[0-9a-zA-Z-#]*)/edit-transaction/$",
        login_required(form_views.AccountUpdateTransactionView.as_view()),
        name="delete_transaction"),
    # account/bittrex/delete-transaction/
    url(r"^account/(?P<slug>[0-9a-zA-Z-#]*)/delete-transaction/$",
        login_required(form_views.AccountDeleteTransactionView.as_view()),
        name="delete_transaction"),

    # add-timespan/
    url(r"^add-timespan/$",
        login_required(form_views.IndexCreateTimespanView.as_view()),
        name="add_timespan"),
    # set-timespan/
    url(r"^set-timespan/$",
        login_required(form_views.IndexUpdateActiveOnTimespanView.as_view()),
        name="set_timespan"),
    # delete-timespan/
    url(r"^delete-timespan/$",
        login_required(form_views.IndexDeleteTimespanView.as_view()),
        name="delete_timespan"),

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
