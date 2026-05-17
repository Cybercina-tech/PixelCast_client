"""
Installation Check Middleware

Intercepts all requests and checks if installation is completed.
If installed.lock does NOT exist and the URL is not /api/setup/*,
returns 503 status or redirects to setup.
"""
import logging
from django.http import JsonResponse, HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin
from .utils import is_installed

logger = logging.getLogger(__name__)


class InstallationCheckMiddleware(MiddlewareMixin):
    """
    Middleware that checks if installation is completed.
    
    If installed.lock does NOT exist:
    - Allows access to /api/setup/* endpoints
    - Allows access to static/media files
    - Returns 503 for API requests
    - Redirects web requests to /install (or returns 503)
    """
    
    # Paths that should be allowed even if installation is not completed
    ALLOWED_PATHS = [
        '/api/setup/',  # All setup endpoints
        '/install',
        '/setup',
        # Public marketing JSON (SPA may call these before installed.lock exists)
        '/api/public/pricing/',
        '/api/public/deployment/',
        '/api/public/downloads/',
        '/static/',
        '/media/',
        '/favicon.ico',
    ]
    
    def process_request(self, request):
        """
        Check if installation is completed. If not, block access except to setup endpoints.
        
        Returns:
            None: If request should proceed normally
            JsonResponse: If API request and installation not completed (503 status)
            HttpResponseRedirect: If web request and installation not completed
        """
        # Skip check if installation is already completed
        if is_installed():
            return None
        
        # Allow access to setup endpoints and static/media files
        path = request.path
        if any(path.startswith(allowed) for allowed in self.ALLOWED_PATHS):
            return None
        
        # Log blocked request
        logger.warning(
            f"Blocked request to {path} - installation not completed",
            extra={
                'path': path,
                'method': request.method,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )
        
        # For API requests, return 503 Service Unavailable
        if path.startswith('/api/'):
            return JsonResponse({
                'error': 'installation_required',
                'message': 'Installation is required before accessing the API. Please complete the installation wizard.',
                'status': 'not_installed'
            }, status=503)
        
        # For web requests, check if it's an AJAX/JSON request
        if request.headers.get('Accept', '').startswith('application/json') or \
           request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'installation_required',
                'message': 'Installation is required. Please complete the installation wizard.',
                'status': 'not_installed',
                'redirect': '/install'
            }, status=503)
        
        # Regular browser navigation should be redirected to installer.
        return HttpResponseRedirect('/install')
