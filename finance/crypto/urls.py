from django.contrib.auth.decorators import login_required
from django.conf.urls import url

from . import views


app_name = "crypto"


urlpatterns = [
    # API DATA
    # api-data/index/
    url(r"^api-data/index/$", login_required(views.IndexData.as_view()), name="api_data_index"),
    # api-data/account/comdirect/
    url(r"^api-data/account/(?P<slug>[0-9a-zA-Z-#]*)/$", login_required(
        views.AccountData.as_view()), name="api_data_account"),
    # api-data/assets
    url(r"^api-data/assets/$", login_required(views.AssetsData.as_view()), name="api_data_assets"),
    # api-data/asset/bitcoin/
    url(r"^api-data/asset/(?P<slug>[0-9a-zA-Z-#]*)/$", login_required(views.AssetData.as_view()),
        name="api_data_asset"),


    # FUNCTIONS
    # update-movie/
    url(r"^update-movies", login_required(views.update_movies), name="update_movies"),

    # update-prices/
    url(r"^update-prices/$", login_required(views.update_prices), name="update_prices"),

    # add-account/
    url(r"^add-account/$", login_required(views.add), name="add_account"),

    # add-asset/
    url(r"^add-asset/$", login_required(views.add), name="add_asset"),
    # delete-asset/
    url(r"^delete-asset/$", login_required(views.delete), name="delete_asset"),

    # asset/bitcoin/add-price/
    url(r"^add-price/$", login_required(views.add), name="add_price"),

    # add-trade/
    url(r"^add-trade/$", login_required(views.add), name="add_trade"),
    # delete-trade/
    url(r"^delete-trade/$", login_required(views.delete), name="delete_trade"),

    # account/comdirect/move-asset/
    url(r"^account/(?P<slug>[0-9a-zA-Z-#]*)/move-asset/$", login_required(views.move_asset),
        name="move_asset"),

    # asset/bitcoin/delete-price/
    url(r"^asset/(?P<slug>[0-9a-zA-Z-#]*)/delete-price/$", login_required(views.delete),
        name="delete_price"),


    # PAGES
    # index
    url(r"^$", login_required(views.CryptoView.as_view()), name="index"),
    # account/comdirect/
    url(r"^account/(?P<slug>[0-9a-zA-Z-#]*)/$", login_required(views.AccountView.as_view()),
        name="account"),
    # asset/bitcoin/
    url(r"^asset/(?P<slug>[0-9a-zA-Z-#]*)/$", login_required(views.AssetView.as_view()),
        name="asset"),
]


handler400 = "finance.core.views.error_400_view"
handler403 = "finance.core.views.error_403_view"
handler404 = "finance.core.views.error_404_view"
handler500 = "finance.core.views.error_500_view"
