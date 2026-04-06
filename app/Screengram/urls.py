"""
URL configuration for PixelCast Signage (package: Screengram).

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('example/', include('my_app.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import JsonResponse
from core.deployment import is_client_deployment
from core.public_views import (
    public_config as public_config_view,
    public_deployment as public_deployment_view,
    public_pricing,
)
from rest_framework.routers import DefaultRouter
from log.views import ErrorLogViewSet
from templates.views import qr_action_redirect

# Create router for admin endpoints
admin_router = DefaultRouter()
admin_router.register(r'errors', ErrorLogViewSet, basename='error-log')


def public_downloads(request):
    """Public JSON for player app download URLs (no authentication)."""
    apk_url = getattr(settings, 'ANDROID_TV_APK_URL', None) or ''
    return JsonResponse({'android_tv_apk_url': apk_url})


_client_deploy = is_client_deployment(getattr(settings, 'DEPLOYMENT_MODE', None))

urlpatterns = [
    path('admin/', admin.site.urls),
    path('qr/<slug:slug>/', qr_action_redirect, name='qr-action-redirect'),
    
    # Setup/Installation endpoints (must be before other API routes)
    path('api/setup/', include('setup.urls')),
    path('api/license/', include('licensing.urls')),
    path('api/license-registry/v1/', include('licensing.registry_urls')),
]

# Platform operator / SaaS admin APIs — not mounted in client (single-tenant) deployments
if not _client_deploy:
    urlpatterns += [
        path('api/platform/tickets/', include('tickets.platform_urls')),
        path('api/platform/', include('saas_platform.urls')),
    ]

urlpatterns += [
    # THE IoT ESCAPE PLAN: IoT endpoints outside /api/ namespace to bypass strict security filters
    # This allows IoT devices to communicate without authentication middleware interference
    path('iot/', include('signage.urls')),  # IoT endpoints (heartbeat, template) - bypasses /api/ security
    
    # LAST RESORT: Public IoT endpoints (keeping for backward compatibility)
    path('public-iot/', include('signage.urls')),  # Public IoT endpoints (heartbeat, template)
    
    # Lightweight health probe used by frontend footer/status checks.
    path('api/health/', lambda request: JsonResponse({'status': 'ok'})),
    path('api/public/downloads/', public_downloads, name='public-downloads'),
    path('api/public/deployment/', public_deployment_view, name='public-deployment'),
    path('api/config/', public_config_view, name='public-config'),
]

if not _client_deploy:
    urlpatterns.append(path('api/public/pricing/', public_pricing, name='public-pricing'))

urlpatterns += [
    path('api/', include('accounts.urls')),
    path('api/', include('commands.urls')),
    path('api/', include('signage.urls')),  # Keep original for other endpoints
    path('api/', include('templates.urls')),
    path('api/', include('bulk_operations.urls')),  # Bulk operations endpoints
    path('api/', include('content_validation.urls')),  # Content validation endpoints
    path('api/', include('analytics.urls')),  # Analytics dashboard endpoints
    path('api/tickets/', include('tickets.urls')),  # Requester ticket API
    path('api/core/', include('core.urls')),  # Core infrastructure (audit, backup)
    path('api/logs/', include('log.urls')),
    path('api/admin/', include(admin_router.urls)),  # Admin-only endpoints (errors)
    path('', include('api_docs.urls')),  # API documentation (Swagger/OpenAPI)
]

# Uploaded media: django.conf.urls.static.static() only registers routes when DEBUG=True.
# With DEBUG=False (common in Docker/.env), that helper adds nothing, but nginx still
# proxies /media/ to Django — without an explicit route, all media URLs return 404.
_serve_local_disk_media = (
    bool(getattr(settings, 'MEDIA_ROOT', None))
    and bool(getattr(settings, 'MEDIA_URL', None))
    and not getattr(settings, 'USE_S3_STORAGE', False)
)

if _serve_local_disk_media:
    if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    else:
        media_prefix = settings.MEDIA_URL.lstrip('/')
        urlpatterns += [
            re_path(
                rf'^{media_prefix}(?P<path>.*)$',
                serve,
                {'document_root': settings.MEDIA_ROOT},
            ),
        ]
