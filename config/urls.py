from django.conf.urls.static import static
from django.shortcuts import redirect
from django.urls import include
from django.contrib import admin
from django.conf import settings
from django.urls import path

urlpatterns = [
    path('', lambda request: redirect('users/redirect/', permanent=False)),
    path('overview/', include('apps.overview.urls')),
    path('users/', include('apps.users.urls')),
    path('banking/', include('apps.banking.urls')),
    path('crypto/', include('apps.crypto.urls')),
    path('alternative/', include('apps.alternative.urls')),
    path('stocks/', include('apps.stocks.urls'))
]

if settings.DEBUG:
    # static and media
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # admin
    urlpatterns += [path('admin/', admin.site.urls), ]

    # debug toolbar
    import debug_toolbar

    urlpatterns += [path('__debug__/', include(debug_toolbar.urls)), ]

    # show the error views
    from django.views.generic import TemplateView

    urlpatterns += path('400/', TemplateView.as_view(template_name='400.html')),
    urlpatterns += path('403/', TemplateView.as_view(template_name='403.html')),
    urlpatterns += path('404/', TemplateView.as_view(template_name='404.html')),
    urlpatterns += path('500/', TemplateView.as_view(template_name='500.html')),
