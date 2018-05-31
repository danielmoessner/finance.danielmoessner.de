from django.conf.urls import url

from finance.users.views import views
from finance.users.views import form_views
from django.contrib.auth.decorators import login_required


app_name = "users"
urlpatterns = [
    # PAGE
    # signup/
    url(r"^signup/$", views.signup, name="signup"),
    # login/
    url(r"^login/$", views.login, name="login"),
    # moesibert/
    url(r"^(?P<slug>[a-zA-Z@.+_-]*)/$", login_required(views.SettingsView.as_view()),
        name="settings"),

    # ADD / EDIT / DELETE
    # moesibert/edit-user/
    url(r"^(?P<slug>[a-zA-Z@.+_-]*)/edit-user/$",
        login_required(form_views.SettingsEditUserView.as_view()), name="edit_user"),
    # moesibert/edit-user-password/
    url(r"^(?P<slug>[a-zA-Z@.+_-]*)/edit-user-password/$",
        login_required(form_views.SettingsEditUserPasswordView.as_view()),
        name="edit_user_password"),
    # moesibert/edit-user-specials/
    url(r"^(?P<slug>[a-zA-Z@.+_-]*)/edit-user-specials/$",
        login_required(form_views.SettingsEditUserSpecialsView.as_view()),
        name="edit_user_specials"),

    # moesibert/add-banking-depot/
    url(r"^(?P<slug>[a-zA-Z@.+_-]*)/add-banking-depot/$",
        login_required(form_views.SettingsAddBankingDepotView.as_view()),
        name="add_banking_depot"),
    # moesibert/edit-banking-depot/
    url(r"^(?P<slug>[a-zA-Z@.+_-]*)/edit-banking-depot/$",
        login_required(form_views.SettingsEditBankingDepotView.as_view()),
        name="edit_banking_depot"),
    # moesibert/delete-banking-depot/
    url(r"^(?P<slug>[a-zA-Z@.+_-]*)/delete-banking-depot/$",
        login_required(form_views.SettingsDeleteBankingDepotView.as_view()),
        name="delete_banking_depot"),

    # moesibert/add-crypto-depot/
    url(r"^(?P<slug>[a-zA-Z@.+_-]*)/add-crypto-depot/$",
        login_required(form_views.SettingsAddCryptoDepotView.as_view()), name="add_crypto_depot"),
    # moesibert/edit-crypto-depot/
    url(r"^(?P<slug>[a-zA-Z@.+_-]*)/edit-crypto-depot/$",
        login_required(form_views.SettingsEditCryptoDepotView.as_view()),
        name="edit_crypto_depot"),
    # moesibert/delete-crypto-depot/
    url(r"^(?P<slug>[a-zA-Z@.+_-]*)/delete-crypto-depot/$",
        login_required(form_views.SettingsDeleteCryptoDepotView.as_view()),
        name="delete_crypto_depot"),

    # CHANGE STATE / UPDATE
    # moesibert/logout/
    url(r"^(?P<slug>[a-zA-Z@.+_-]*)/logout/$", views.logout, name="logout"),

    # moesibert/init-banking/
    url(r"^(?P<slug>[a-zA-Z@.+_-]*)/init-banking/$", views.init_banking, name="init_banking"),
    # moesibert/set-banking-depot-active/
    url(r"^(?P<slug>[a-zA-Z@.+_-]*)/set-banking-depot-active/(?P<pk>\d+)/$",
        login_required(views.set_banking_depot_active),
        name="set_banking_depot_active"),

    # moesibert/set-crypto-depot-active/
    url(r"^(?P<slug>[a-zA-Z@.+_-]*)/set-crypto-depot-active/(?P<pk>\d+)/$",
        login_required(views.set_crypto_depot_active),
        name="set_crypto_depot_active"),

]
