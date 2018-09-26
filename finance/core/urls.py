from django.conf.urls import url

from finance.core import views


app_name = "core"


urlpatterns = [
    # PAGES
    url(r"^data-protection/$", views.DataProtectionView.as_view(), name="data_protection"),
    url(r"^imprint/$", views.ImprintView.as_view(), name="imprint"),
    url(r"^terms-of-use/$", views.TermsOfUseView.as_view(), name="terms_of_use"),
    url(r"", views.IndexView.as_view(), name="index"),
]


