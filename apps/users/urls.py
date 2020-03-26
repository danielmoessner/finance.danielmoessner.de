from django.urls import path

from apps.users import formviews, views

app_name = 'users'


urlpatterns = [
    # pages
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('signin/', views.SignInView.as_view(), name='signin'),
    path('users/<int:pk>/', views.IndexView.as_view(), name='settings'),

    # logout
    path('logout/', views.SignOutView.as_view(), name='logout'),

    # smart redirect
    path('redirect/', views.RedirectView.as_view(), name='redirect'),

    # settings
    path('users/<int:pk>/edit/', formviews.EditUserSettingsView.as_view(), name='edit_user'),
    path('users/<int:pk>/edit-password/', formviews.EditUserPasswordSettingsView.as_view(), name='edit_user_password'),
    path('users/<int:pk>/edit-general/', formviews.EditUserGeneralSettingsView.as_view(), name='edit_user_general'),
    path('users/<int:pk>/edit-crypto/', formviews.EditUserCryptoSettingsView.as_view(), name='edit_user_crypto'),

    # generate random data
    path('users/<int:pk>/generate-banking/', views.init_banking, name='init_banking'),
    path('users/<int:pk>/generate-crypto/', views.init_crypto, name='init_crypto'),
    path('users/<int:pk>/generate-alternative/', views.init_alternative, name='init_alternative'),
]
