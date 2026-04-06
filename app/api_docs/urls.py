"""
URL configuration for API documentation endpoints.
"""
from django.urls import path
from .views import (
    ProtectedSpectacularAPIView,
    ProtectedSpectacularSwaggerView,
    ProtectedSpectacularRedocView,
)

app_name = 'api_docs'

urlpatterns = [
    # OpenAPI Schema (JSON/YAML)
    path('api/schema/', ProtectedSpectacularAPIView.as_view(), name='schema'),
    
    # Swagger UI (Interactive)
    path('api/docs/', ProtectedSpectacularSwaggerView.as_view(url_name='api_docs:schema'), name='swagger-ui'),
    
    # ReDoc (Alternative UI) - More readable format
    path('api/redoc/', ProtectedSpectacularRedocView.as_view(url_name='api_docs:schema'), name='redoc'),
    
    # Legacy paths (redirect to new paths)
    path('docs/', ProtectedSpectacularSwaggerView.as_view(url_name='api_docs:schema'), name='docs'),
    path('swagger/', ProtectedSpectacularSwaggerView.as_view(url_name='api_docs:schema'), name='swagger'),
]
