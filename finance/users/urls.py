from django.conf.urls import url

from finance.users.views import views
from finance.users.views import form_views
from django.contrib.auth.decorators import login_required


app_name = "users"


urlpatterns = [
    # PAGE
    # signup/
    url(r"^signup/$", views.SignUpView.as_view(), name="signup"),
    # login/
    url(r"^signin/$", views.SignInView.as_view(), name="signin"),
    # moesibert/
    url(r"^$", login_required(views.SettingsView.as_view()), name="settings"),

    # ADD / EDIT / DELETE
    url(r"^edit-user/(?P<slug>[\w-]+)/$",
        login_required(form_views.EditUserSettingsView.as_view()),
        name="edit_user"),
    url(r"^edit-user-password/(?P<slug>[\w-]+)/$",
        login_required(form_views.EditUserPasswordSettingsView.as_view()),
        name="edit_user_password"),
    url(r"^edit-user-general/(?P<slug>[\w-]+)/$",
        login_required(form_views.EditUserGeneralSettingsView.as_view()),
        name="edit_user_general"),
    url(r"^edit-user-crypto/(?P<slug>[\w-]+)/$",
        login_required(form_views.EditUserCryptoSettingsView.as_view()),
        name="edit_user_crypto"),

    # CHANGE STATE / UPDATE
    # moesibert/logout/
    url(r"^logout/$", views.LogoutView.as_view(), name="logout"),

    # moesibert/init-banking/
    url(r"^init-banking/$", views.init_banking, name="init_banking"),
    # moesibert/set-banking-depot-active/
    url(r"^(?P<slug>[0-9a-zA-Z@.+_-]*)/set-banking-depot-active/(?P<pk>\d+)/$",
        login_required(views.set_banking_depot_active),
        name="set_banking_depot_active"),

    # moesibert/init-crypto/
    url(r"^init-crypto/$", views.init_crypto, name="init_crypto"),
    # moesibert/set-crypto-depot-active/
    url(r"^(?P<slug>[0-9a-zA-Z@.+_-]*)/set-crypto-depot-active/(?P<pk>\d+)/$",
        login_required(views.set_crypto_depot_active),
        name="set_crypto_depot_active"),
]
