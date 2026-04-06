"""
Content validation utilities and helpers.

Provides logging and integration with validation system.
"""
import logging
from typing import Dict, Any, Optional
from django.utils import timezone

logger = logging.getLogger(__name__)


def log_validation(
    user_id: int,
    username: str,
    filename: str,
    sanitized_filename: str,
    content_type: str,
    validation_result: Dict[str, Any],
    content_id: Optional[str] = None
) -> None:
    """
    Log content validation for auditing.
    
    Args:
        user_id: User ID who uploaded the content
        username: Username who uploaded the content
        filename: Original filename
        sanitized_filename: Sanitized filename
        content_type: Content type
        validation_result: Result from ContentValidator.validate_content()
        content_id: Optional content ID if saved
    """
    try:
        from log.models import ContentValidationLog
        
        # Determine validation status
        is_valid = validation_result.get('is_valid', False)
        errors = validation_result.get('errors', [])
        
        # Check for security issues
        has_security_risk = any(
            'Security' in err or 'security' in err.lower() or
            'executable' in err.lower() or 'injection' in err.lower()
            for err in errors
        )
        
        if has_security_risk:
            status = 'security_risk'
        elif is_valid:
            status = 'valid'
        elif errors:
            status = 'invalid'
        else:
            status = 'pending'
        
        # Extract security flags
        security_flags = [
            err for err in errors
            if 'Security' in err or 'security' in err.lower() or
               'executable' in err.lower() or 'injection' in err.lower()
        ]
        
        ContentValidationLog.objects.create(
            user_id=user_id,
            username=username,
            content_id=content_id,
            filename=filename,
            sanitized_filename=sanitized_filename,
            content_type=content_type,
            file_size=validation_result.get('metadata', {}).get('file_size'),
            mime_type=validation_result.get('metadata', {}).get('mime_type'),
            validation_status=status,
            is_valid=is_valid,
            validation_errors=errors,
            validation_warnings=validation_result.get('warnings', []),
            metadata=validation_result.get('metadata', {}),
            security_flags=security_flags,
            timestamp=timezone.now()
        )
    except ImportError:
        # ContentValidationLog model might not exist yet (during migrations)
        logger.warning(
            f"ContentValidationLog model not available. Skipping audit log. "
            f"Filename: {filename}, User: {username}"
        )
    except Exception as e:
        # Log to Django logger if database logging fails
        logger.error(
            f"Failed to create content validation log: {str(e)}. "
            f"Filename: {filename}, User: {username}"
        )
