"""
Audit logging utilities for PixelCast Signage.

Provides functions to log critical system actions with full context.
"""
import json
from typing import Optional, Dict, Any
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.utils import timezone
from core.models import AuditLog
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class AuditLogger:
    """
    Centralized audit logging utility.
    """

    # Severity mappings for common actions
    ACTION_SEVERITY = {
        'create': 'medium',
        'read': 'low',
        'update': 'medium',
        'delete': 'high',
        'activate': 'medium',
        'deactivate': 'medium',
        'execute': 'medium',
        'login': 'low',
        'logout': 'low',
        'password_change': 'high',
        'role_change': 'critical',
        'bulk_operation': 'high',
        'backup': 'medium',
        'restore': 'critical',
        'export': 'medium',
        'import': 'high',
    }

    @classmethod
    def get_request_info(cls, request) -> Dict[str, Any]:
        """Extract request information for audit logging."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', 'unknown')

        user_agent = request.META.get('HTTP_USER_AGENT', '')

        return {
            'ip_address': ip_address,
            'user_agent': user_agent,
        }

    @classmethod
    def log_action(
        cls,
        action_type: str,
        user: Optional[User] = None,
        resource: Optional[Model] = None,
        resource_type: Optional[str] = None,
        resource_name: Optional[str] = None,
        description: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        severity: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request: Optional[Any] = None,
    ) -> AuditLog:
        """
        Log an audit event.

        Args:
            action_type: Type of action (from AuditLog.ACTION_TYPES)
            user: User who performed the action
            resource: Model instance that was affected
            resource_type: Type of resource (if resource not provided)
            resource_name: Name of resource (if resource not provided)
            description: Human-readable description
            changes: Dict with 'before' and 'after' keys
            metadata: Additional metadata
            success: Whether action was successful
            error_message: Error message if failed
            severity: Severity level (auto-determined if not provided)
            ip_address: Client IP address
            user_agent: Client user agent
            request: Django request object (used to extract IP/user_agent)

        Returns:
            Created AuditLog instance
        """
        # Extract info from request if provided
        if request:
            request_info = cls.get_request_info(request)
            ip_address = ip_address or request_info['ip_address']
            user_agent = user_agent or request_info['user_agent']
            if not user and hasattr(request, 'user'):
                user = request.user

        # Extract resource info
        if resource:
            content_type = ContentType.objects.get_for_model(resource)
            object_id = str(resource.pk)
            if not resource_type:
                resource_type = resource.__class__.__name__
            if not resource_name:
                resource_name = str(resource)
        else:
            content_type = None
            object_id = None

        # Determine severity
        if not severity:
            severity = cls.ACTION_SEVERITY.get(action_type, 'medium')

        # Get user info
        username = ''
        user_role = ''
        if user:
            username = getattr(user, 'username', '') or str(user)
            user_role = getattr(user, 'role', '') or ''

        # Create audit log entry
        try:
            audit_log = AuditLog.objects.create(
                user=user,
                username=username,
                user_role=user_role,
                ip_address=ip_address,
                user_agent=user_agent or '',
                action_type=action_type,
                severity=severity,
                content_type=content_type,
                object_id=object_id,
                resource_type=resource_type or '',
                resource_name=resource_name or '',
                description=description or '',
                changes=changes or {},
                metadata=metadata or {},
                success=success,
                error_message=error_message or '',
            )

            logger.info(
                f"Audit log created: {action_type} by {username} on {resource_type or 'unknown'}"
            )

            return audit_log

        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Don't raise - audit logging failures should not break the application
            return None

    @classmethod
    def log_crud(
        cls,
        action: str,  # 'create', 'update', 'delete'
        instance: Model,
        user: Optional[User] = None,
        changes: Optional[Dict[str, Any]] = None,
        request: Optional[Any] = None,
    ) -> AuditLog:
        """Log CRUD operation."""
        return cls.log_action(
            action_type=action,
            user=user,
            resource=instance,
            description=f"{action.capitalize()}d {instance.__class__.__name__} '{instance}'",
            changes=changes,
            request=request,
        )

    @classmethod
    def log_authentication(
        cls,
        action: str,  # 'login' or 'logout'
        user: Optional[User] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        request: Optional[Any] = None,
    ) -> AuditLog:
        """Log authentication event."""
        description = f"User {'logged in' if action == 'login' else 'logged out'}"
        if not success:
            description += f" (failed: {error_message})"

        return cls.log_action(
            action_type=action,
            user=user,
            description=description,
            success=success,
            error_message=error_message,
            request=request,
        )

    @classmethod
    def log_bulk_operation(
        cls,
        operation_type: str,
        resource_type: str,
        item_count: int,
        success_count: int,
        failure_count: int,
        user: Optional[User] = None,
        request: Optional[Any] = None,
    ) -> AuditLog:
        """Log bulk operation."""
        description = (
            f"Bulk {operation_type}: {item_count} {resource_type} items "
            f"({success_count} succeeded, {failure_count} failed)"
        )

        return cls.log_action(
            action_type='bulk_operation',
            user=user,
            resource_type=resource_type,
            description=description,
            metadata={
                'operation_type': operation_type,
                'item_count': item_count,
                'success_count': success_count,
                'failure_count': failure_count,
            },
            success=failure_count == 0,
            request=request,
        )

    @classmethod
    def log_backup(
        cls,
        backup_type: str,
        status: str,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        error_message: Optional[str] = None,
        user: Optional[User] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log backup operation."""
        description = f"Backup {backup_type}: {status}"
        if file_path:
            description += f" ({file_path})"

        return cls.log_action(
            action_type='backup',
            user=user,
            resource_type='System',
            description=description,
            metadata={
                'backup_type': backup_type,
                'status': status,
                'file_path': file_path,
                'file_size': file_size,
                **(metadata or {})
            },
            success=status == 'completed',
            error_message=error_message,
            severity='medium' if status == 'completed' else 'high',
        )


# Convenience functions
def log_action(*args, **kwargs) -> AuditLog:
    """Convenience function to log an action."""
    return AuditLogger.log_action(*args, **kwargs)


def log_crud(*args, **kwargs) -> AuditLog:
    """Convenience function to log CRUD operation."""
    return AuditLogger.log_crud(*args, **kwargs)


def log_authentication(*args, **kwargs) -> AuditLog:
    """Convenience function to log authentication."""
    return AuditLogger.log_authentication(*args, **kwargs)


def log_bulk_operation(*args, **kwargs) -> AuditLog:
    """Convenience function to log bulk operation."""
    return AuditLogger.log_bulk_operation(*args, **kwargs)


def log_backup(*args, **kwargs) -> AuditLog:
    """Convenience function to log backup."""
    return AuditLogger.log_backup(*args, **kwargs)
