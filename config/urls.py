"""moneymanagement URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.conf.urls import include
from django.contrib import admin
from django.conf import settings
from django.urls import path


urlpatterns = [
    path('', lambda request: redirect('core/', permanent=False)),
    path('user/', include('finance.users.urls')),
    path('banking/', include('finance.banking.urls')),
    path('crypto/', include('finance.crypto.urls')),
    path('alternative/', include('finance.alternative.urls')),
    path('core/', include('finance.core.urls')),
]


handler400 = "finance.core.views.error_400_view"
handler403 = "finance.core.views.error_403_view"
handler404 = "finance.core.views.error_404_view"
handler500 = "finance.core.views.error_500_view"


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('admin/', admin.site.urls), ]
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls)), ]
