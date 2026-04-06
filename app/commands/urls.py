from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommandViewSet, command_receive_endpoint

# Create router for ViewSets
router = DefaultRouter()
router.register(r'commands', CommandViewSet, basename='command')

urlpatterns = [
    # Router URLs (includes /api/commands/ for ViewSet)
    path('', include(router.urls)),
    
    # HTTP fallback endpoint for screens to receive commands
    path('screens/command-receive/', command_receive_endpoint, name='command-receive'),
]
