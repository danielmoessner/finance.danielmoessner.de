from django.urls import path

from finance.core import views


app_name = 'core'


urlpatterns = [
    # PAGES
    path('data-protection/', views.DataProtectionView.as_view(), name='data_protection'),
    path('imprint/', views.ImprintView.as_view(), name='imprint'),
    path('terms-of-use/', views.TermsOfUseView.as_view(), name='terms_of_use'),
    path('', views.IndexView.as_view(), name='index'),
    path('old-index/', views.OldIndexView.as_view(), name='old_index'),
    path('redirect/', views.RedirectView.as_view(), name='redirect'),
    path('page/<slug>/', views.PageView.as_view(), name='page')
]


