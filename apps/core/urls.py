from django.urls import path, re_path
from apps.core import views


app_name = 'core'


urlpatterns = [
    # PAGES
    path('data-protection/', views.DataProtectionView.as_view(), name='data_protection'),
    path('imprint/', views.ImprintView.as_view(), name='imprint'),
    path('terms-of-use/', views.TermsOfUseView.as_view(), name='terms_of_use'),
    path('', views.IndexView.as_view(), name='index'),
    path('old-index/', views.OldIndexView.as_view(), name='old_index'),
    path('page/<slug>/', views.PageView.as_view(), name='page'),
    re_path(r'^(?!static).*(js|images|css|icons).*$', views.StaticRedirectView.as_view(), name='static_redirect')
]


