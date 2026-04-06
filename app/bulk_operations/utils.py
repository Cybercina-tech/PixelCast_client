"""
Common utilities for bulk operations.

Provides transaction management, validation, rate limiting, logging,
and error handling for bulk operations.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple, Callable
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class BulkOperationError(Exception):
    """Custom exception for bulk operation errors"""
    pass


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass


class BulkOperationResult:
    """
    Represents the result of a bulk operation for a single item.
    """
    def __init__(self, item_id: str, status: str, message: str = '', data: Any = None):
        self.item_id = item_id
        self.status = status  # 'success' or 'failure'
        self.message = message
        self.data = data
    
    def to_dict(self):
        """Convert to dictionary for API response"""
        result = {
            'item_id': self.item_id,
            'status': self.status,
            'message': self.message
        }
        if self.data is not None:
            result['data'] = self.data
        return result


class BulkOperationResponse:
    """
    Represents the complete response for a bulk operation.
    """
    def __init__(self):
        self.results: List[BulkOperationResult] = []
        self.success_count = 0
        self.failure_count = 0
        self.total_count = 0
    
    def add_result(self, result: BulkOperationResult):
        """Add a result to the response"""
        self.results.append(result)
        self.total_count += 1
        if result.status == 'success':
            self.success_count += 1
        else:
            self.failure_count += 1
    
    def to_dict(self, include_details: bool = True):
        """Convert to dictionary for API response"""
        response = {
            'total_count': self.total_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': round((self.success_count / self.total_count * 100) if self.total_count > 0 else 0, 2)
        }
        if include_details:
            response['results'] = [r.to_dict() for r in self.results]
        return response
    
    def to_response(self, include_details: bool = True, http_status: int = status.HTTP_200_OK):
        """Convert to DRF Response"""
        data = self.to_dict(include_details)
        if self.failure_count > 0 and self.success_count == 0:
            http_status = status.HTTP_400_BAD_REQUEST
        elif self.failure_count > 0:
            http_status = status.HTTP_207_MULTI_STATUS  # Multi-Status for partial success
        return Response(data, status=http_status)


def validate_item_ids(item_ids: List[str], max_items: int = 1000) -> Tuple[List[str], List[str]]:
    """
    Validate and sanitize item IDs.
    
    Args:
        item_ids: List of item IDs (can be UUIDs or other IDs)
        max_items: Maximum number of items allowed (default: 1000)
    
    Returns:
        Tuple of (valid_ids, invalid_ids)
    
    Raises:
        BulkOperationError: If validation fails critically
    """
    if not item_ids:
        raise BulkOperationError("No item IDs provided")
    
    if len(item_ids) > max_items:
        raise BulkOperationError(
            f"Too many items. Maximum {max_items} items allowed, got {len(item_ids)}"
        )
    
    # Remove duplicates while preserving order
    seen = set()
    unique_ids = []
    for item_id in item_ids:
        if item_id not in seen:
            seen.add(item_id)
            unique_ids.append(item_id)
    
    # Validate format (basic UUID validation)
    valid_ids = []
    invalid_ids = []
    
    for item_id in unique_ids:
        if not item_id or not isinstance(item_id, str):
            invalid_ids.append(str(item_id) if item_id else 'empty')
            continue
        
        # Basic validation: should be alphanumeric with dashes/underscores (UUID format)
        cleaned_id = item_id.strip()
        if len(cleaned_id) < 8 or len(cleaned_id) > 128:
            invalid_ids.append(item_id)
            continue
        
        # Check for potentially malicious content
        if any(char in cleaned_id for char in ['<', '>', '"', "'", ';', '&', '|', '$', '`']):
            invalid_ids.append(item_id)
            continue
        
        valid_ids.append(cleaned_id)
    
    return valid_ids, invalid_ids


def check_rate_limit(
    user_id: int,
    operation_type: str,
    item_count: int,
    limit_per_minute: int = 100,
    limit_per_hour: int = 1000
) -> None:
    """
    Check rate limiting for bulk operations.
    
    Args:
        user_id: User ID
        operation_type: Type of operation (e.g., 'bulk_delete', 'bulk_update')
        item_count: Number of items in this operation
        limit_per_minute: Maximum operations per minute (default: 100)
        limit_per_hour: Maximum operations per hour (default: 1000)
    
    Raises:
        RateLimitExceeded: If rate limit is exceeded
    """
    now = timezone.now()
    minute_key = f"bulk_rate_limit:{user_id}:{operation_type}:minute:{now.minute}"
    hour_key = f"bulk_rate_limit:{user_id}:{operation_type}:hour:{now.hour}"
    
    # Get current counts
    minute_count = cache.get(minute_key, 0)
    hour_count = cache.get(hour_key, 0)
    
    # Check limits
    if minute_count + item_count > limit_per_minute:
        raise RateLimitExceeded(
            f"Rate limit exceeded: {minute_count + item_count} operations in this minute "
            f"(limit: {limit_per_minute}). Please try again later."
        )
    
    if hour_count + item_count > limit_per_hour:
        raise RateLimitExceeded(
            f"Rate limit exceeded: {hour_count + item_count} operations in this hour "
            f"(limit: {limit_per_hour}). Please try again later."
        )
    
    # Update counters
    cache.set(minute_key, minute_count + item_count, timeout=60)  # Expire after 60 seconds
    cache.set(hour_key, hour_count + item_count, timeout=3600)  # Expire after 1 hour


def log_bulk_operation(
    user_id: int,
    username: str,
    operation_type: str,
    module: str,
    item_ids: List[str],
    success_count: int,
    failure_count: int,
    details: Optional[Dict[str, Any]] = None
):
    """
    Log bulk operation for auditing.
    
    Args:
        user_id: User ID who performed the operation
        username: Username who performed the operation
        operation_type: Type of operation (e.g., 'bulk_delete', 'bulk_update')
        module: Module name (e.g., 'screens', 'templates')
        item_ids: List of item IDs affected
        success_count: Number of successful operations
        failure_count: Number of failed operations
        details: Optional additional details
    """
    try:
        from log.models import BulkOperationLog
        
        BulkOperationLog.objects.create(
            user_id=user_id,
            username=username,
            operation_type=operation_type,
            module=module,
            item_ids=item_ids,
            item_count=len(item_ids),
            success_count=success_count,
            failure_count=failure_count,
            details=details or {},
            timestamp=timezone.now()
        )
    except ImportError:
        # BulkOperationLog model might not exist yet (during migrations)
        logger.warning(
            f"BulkOperationLog model not available. Skipping audit log. "
            f"Operation: {operation_type}, Module: {module}, User: {username}"
        )
    except Exception as e:
        # Log to Django logger if database logging fails
        logger.error(
            f"Failed to create bulk operation log: {str(e)}. "
            f"Operation: {operation_type}, Module: {module}, User: {username}"
        )


def execute_bulk_operation(
    item_ids: List[str],
    operation_func: Callable[[str], Tuple[bool, str, Any]],
    operation_name: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    module: Optional[str] = None,
    use_transaction: bool = True,
    continue_on_error: bool = True,
    rate_limit_per_minute: int = 100,
    rate_limit_per_hour: int = 1000
) -> BulkOperationResponse:
    """
    Execute a bulk operation with proper error handling, logging, and rate limiting.
    
    Args:
        item_ids: List of item IDs to process
        operation_func: Function that takes item_id and returns (success, message, data)
        operation_name: Name of the operation for logging (e.g., 'bulk_delete')
        user_id: User ID for rate limiting and logging
        username: Username for logging
        module: Module name for logging
        use_transaction: Whether to use database transactions
        continue_on_error: Whether to continue processing if one item fails
        rate_limit_per_minute: Rate limit per minute
        rate_limit_per_hour: Rate limit per hour
    
    Returns:
        BulkOperationResponse with results
    """
    response = BulkOperationResponse()
    
    # Validate item IDs
    try:
        valid_ids, invalid_ids = validate_item_ids(item_ids)
        
        # Add invalid IDs as failures
        for invalid_id in invalid_ids:
            response.add_result(BulkOperationResult(
                item_id=invalid_id,
                status='failure',
                message='Invalid item ID format'
            ))
        
        if not valid_ids:
            return response
        
        # Check rate limiting
        if user_id:
            try:
                check_rate_limit(
                    user_id=user_id,
                    operation_type=operation_name,
                    item_count=len(valid_ids),
                    limit_per_minute=rate_limit_per_minute,
                    limit_per_hour=rate_limit_per_hour
                )
            except RateLimitExceeded as e:
                # All items fail due to rate limiting
                for item_id in valid_ids:
                    response.add_result(BulkOperationResult(
                        item_id=item_id,
                        status='failure',
                        message=str(e)
                    ))
                return response
        
        # Execute operations
        if use_transaction:
            # Use transaction per item (partial success allowed)
            for item_id in valid_ids:
                try:
                    with transaction.atomic():
                        success, message, data = operation_func(item_id)
                        response.add_result(BulkOperationResult(
                            item_id=item_id,
                            status='success' if success else 'failure',
                            message=message,
                            data=data
                        ))
                except Exception as e:
                    error_msg = str(e)
                    response.add_result(BulkOperationResult(
                        item_id=item_id,
                        status='failure',
                        message=error_msg
                    ))
                    if not continue_on_error:
                        break
        else:
            # No transaction, execute directly
            for item_id in valid_ids:
                try:
                    success, message, data = operation_func(item_id)
                    response.add_result(BulkOperationResult(
                        item_id=item_id,
                        status='success' if success else 'failure',
                        message=message,
                        data=data
                    ))
                except Exception as e:
                    error_msg = str(e)
                    response.add_result(BulkOperationResult(
                        item_id=item_id,
                        status='failure',
                        message=error_msg
                    ))
                    if not continue_on_error:
                        break
        
        # Log operation
        if user_id and username and module:
            log_bulk_operation(
                user_id=user_id,
                username=username,
                operation_type=operation_name,
                module=module,
                item_ids=valid_ids,
                success_count=response.success_count,
                failure_count=response.failure_count
            )
        
    except BulkOperationError as e:
        # Critical validation error - all items fail
        for item_id in item_ids:
            response.add_result(BulkOperationResult(
                item_id=str(item_id),
                status='failure',
                message=str(e)
            ))
    
    return response
