"""
API Documentation views.

OpenAPI schema, Swagger UI, and ReDoc are public so buyers and integrators can browse
the API without logging in. Individual API endpoints still enforce auth as configured.
"""
from rest_framework.permissions import AllowAny
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


class ProtectedSpectacularAPIView(SpectacularAPIView):
    """OpenAPI schema (JSON/YAML) — public read."""
    permission_classes = [AllowAny]


class ProtectedSpectacularSwaggerView(SpectacularSwaggerView):
    """Swagger UI — public."""
    permission_classes = [AllowAny]


class ProtectedSpectacularRedocView(SpectacularRedocView):
    """ReDoc — public."""
    permission_classes = [AllowAny]
