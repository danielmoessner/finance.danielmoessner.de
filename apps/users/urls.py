from django.urls import path

from apps.users.views import views
from apps.users.views import form_views


app_name = "users"


urlpatterns = [
    # PAGE
    # signup/
    path("signup/", views.SignUpView.as_view(), name="signup"),
    # login/
    path("signin/", views.SignInView.as_view(), name="signin"),
    # moesibert/
    path("settings/", views.SettingsView.as_view(), name="settings"),

    path('redirect/', views.RedirectView.as_view(), name='redirect'),

    # ADD / EDIT / DELETE
    path("user/<slug>/edit/", form_views.EditUserSettingsView.as_view(), name="edit_user"),
    path("user/<slug>/edit-password/", form_views.EditUserPasswordSettingsView.as_view(), name="edit_user_password"),
    path("user/<slug>/edit-general/", form_views.EditUserGeneralSettingsView.as_view(), name="edit_user_general"),
    path("user/<slug>/edit-crypto/", form_views.EditUserCryptoSettingsView.as_view(), name="edit_user_crypto"),

    # CHANGE STATE / UPDATE
    # logout
    path("logout/", views.SignOutView.as_view(), name="logout"),

    # banking
    path("init-banking/", views.init_banking, name="init_banking"),
    path("<slug>/set-banking-depot-active/<pk>/", views.set_banking_depot_active, name="set_banking_depot_active"),

    # crypto
    path("init-crypto/", views.init_crypto, name="init_crypto"),
    path("<slug>/set-crypto-depot-active/<pk>/", views.set_crypto_depot_active, name="set_crypto_depot_active"),

    # alternative
    path("init-alternative/", views.init_alternative, name="init_alternative"),
    path("<slug>/set-alternative-depot-active/<pk>/", views.set_alternative_depot_active,
         name="set_alternative_depot_active"),
]
