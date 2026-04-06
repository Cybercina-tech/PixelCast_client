from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework.routers import DefaultRouter
from .views import (
    ScreenViewSet,
    heartbeat_endpoint,
    command_pull_endpoint,
    command_response_endpoint,
    iot_command_pull_endpoint,
    iot_command_response_endpoint,
    content_sync_endpoint,
    health_check_endpoint,
    player_template_endpoint,
    generate_pairing_session,
    get_pairing_status,
    bind_pairing_session
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'screens', ScreenViewSet, basename='screen')

urlpatterns = [
    # CRITICAL: Explicit paths MUST come FIRST before router includes to prevent URL shadowing
    # The router's pattern would match /screens/heartbeat/ as /screens/{id}/ if these come after
    path('screens/heartbeat/', csrf_exempt(heartbeat_endpoint), name='screen-heartbeat'),
    path('player/template/', csrf_exempt(player_template_endpoint), name='player-template'),
    
    # IoT Command endpoints (using screen_id authentication)
    path('commands/pending/', csrf_exempt(iot_command_pull_endpoint), name='iot-command-pull'),
    path('commands/status/', csrf_exempt(iot_command_response_endpoint), name='iot-command-response'),
    
    # Other standalone API endpoints
    path('screens/command-pull/', command_pull_endpoint, name='screen-command-pull'),
    path('screens/command-response/', command_response_endpoint, name='screen-command-response'),
    path('screens/content-sync/', content_sync_endpoint, name='screen-content-sync'),
    path('screens/health-check/', health_check_endpoint, name='screen-health-check'),
    # Note: command-receive endpoint is in commands.urls for better organization
    
    # Pairing endpoints
    path('pairing/generate/', generate_pairing_session, name='pairing-generate'),
    path('pairing/status/', get_pairing_status, name='pairing-status'),
    path('pairing/bind/', bind_pairing_session, name='pairing-bind'),
    
    # Router URLs (includes /api/screens/ for ViewSet) - MUST come LAST to prevent shadowing
    path('', include(router.urls)),
]
