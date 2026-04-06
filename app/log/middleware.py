"""
Error logging middleware to capture all server-side errors.
"""
import traceback
import logging
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from .models import ErrorLog

User = get_user_model()
logger = logging.getLogger(__name__)


class ErrorLoggingMiddleware:
    """
    Middleware to capture and log all exceptions that occur during request processing.
    
    This middleware catches exceptions, logs them to the ErrorLog model,
    and then re-raises them so normal error handling can proceed.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        """Process request and catch exceptions"""
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """
        Process exceptions that occur during request handling.
        
        This method is called by Django when an exception is raised
        during view processing. We log it to ErrorLog and then return None
        to let Django's normal error handling proceed.
        """
        try:
            # Get user from request (may be None for unauthenticated requests)
            user = None
            if hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
            
            # Get exception details
            exception_type = type(exception).__name__
            exception_message = str(exception)
            stack_trace = ''.join(traceback.format_exception(
                type(exception),
                exception,
                exception.__traceback__
            ))
            
            # Determine error level based on exception type
            level = 'ERROR'
            if isinstance(exception, (PermissionDenied, ValueError, TypeError)):
                level = 'WARNING'
            elif isinstance(exception, (SystemExit, KeyboardInterrupt)):
                level = 'CRITICAL'
            
            # Get request details
            endpoint = request.path if hasattr(request, 'path') else None
            method = request.method if hasattr(request, 'method') else None
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Create error log entry
            ErrorLog.objects.create(
                level=level,
                message=exception_message,
                user=user,
                stack_trace=stack_trace,
                endpoint=endpoint,
                request_method=method,
                ip_address=ip_address,
                user_agent=user_agent,
                exception_type=exception_type,
                metadata={
                    'request_data': self.get_request_data(request),
                    'query_params': dict(request.GET) if hasattr(request, 'GET') else {},
                }
            )
            
            # Also log to standard Django logger
            logger.error(
                f"Error logged: {exception_type} - {exception_message}",
                exc_info=True,
                extra={
                    'user': user.username if user else None,
                    'endpoint': endpoint,
                    'method': method,
                }
            )
            
        except Exception as e:
            # If error logging itself fails, log to standard logger only
            logger.critical(f"Failed to log error to ErrorLog model: {e}", exc_info=True)
        
        # Return None to let Django's normal error handling proceed
        return None
    
    def get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_request_data(self, request):
        """Safely extract request data for logging"""
        try:
            if hasattr(request, 'body') and request.body:
                # Limit body size to prevent huge logs
                body = request.body[:1000] if len(request.body) > 1000 else request.body
                try:
                    import json
                    return json.loads(body.decode('utf-8'))
                except:
                    return body.decode('utf-8', errors='ignore')
        except Exception:
            pass
        return {}


def log_error(level='ERROR', message='', user=None, stack_trace=None, endpoint=None, 
              exception=None, metadata=None):
    """
    Helper function to manually log errors from anywhere in the codebase.
    
    Usage:
        from log.middleware import log_error
        log_error(
            level='ERROR',
            message='Something went wrong',
            user=request.user,
            endpoint=request.path,
            exception=exception
        )
    """
    try:
        exception_type = None
        exception_message = message
        full_stack_trace = stack_trace
        
        if exception:
            exception_type = type(exception).__name__
            exception_message = str(exception) if not message else message
            if not full_stack_trace:
                import traceback
                full_stack_trace = ''.join(traceback.format_exception(
                    type(exception),
                    exception,
                    exception.__traceback__
                ))
        
        ErrorLog.objects.create(
            level=level,
            message=exception_message,
            user=user,
            stack_trace=full_stack_trace,
            endpoint=endpoint,
            exception_type=exception_type,
            metadata=metadata or {},
        )
    except Exception as e:
        logger.error(f"Failed to log error: {e}", exc_info=True)

