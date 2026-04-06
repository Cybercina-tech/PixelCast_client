from django.urls import path
from .views import (
    LicenseStatusView,
    LicenseActivateView,
    LicenseRevalidateView,
    LicenseProductOverrideView,
)

app_name = "licensing"

urlpatterns = [
    path("status/", LicenseStatusView.as_view(), name="status"),
    path("activate/", LicenseActivateView.as_view(), name="activate"),
    path("revalidate/", LicenseRevalidateView.as_view(), name="revalidate"),
    path("product-id-override/", LicenseProductOverrideView.as_view(), name="product-id-override"),
]
