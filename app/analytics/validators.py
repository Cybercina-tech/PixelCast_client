"""
Input validation for analytics API endpoints.

Provides validators to ensure request parameters are safe and valid.
"""
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta, datetime
from typing import Optional, Tuple
import re


def validate_date_range(
    start_date: Optional[str],
    end_date: Optional[str],
    max_days: int = 365
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Validate and parse date range parameters.
    
    Args:
        start_date: ISO format date string (YYYY-MM-DD) or None
        end_date: ISO format date string (YYYY-MM-DD) or None
        max_days: Maximum allowed date range in days
        
    Returns:
        Tuple of (start_datetime, end_datetime) or (None, None)
        
    Raises:
        ValidationError: If dates are invalid or range exceeds max_days
    """
    start_dt = None
    end_dt = None
    
    # Validate start_date format
    if start_date:
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', start_date):
            raise ValidationError(f"Invalid start_date format. Use YYYY-MM-DD.")
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            start_dt = timezone.make_aware(start_dt)
        except ValueError as e:
            raise ValidationError(f"Invalid start_date: {str(e)}")
    
    # Validate end_date format
    if end_date:
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', end_date):
            raise ValidationError(f"Invalid end_date format. Use YYYY-MM-DD.")
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            # Set to end of day
            end_dt = timezone.make_aware(end_dt.replace(hour=23, minute=59, second=59))
        except ValueError as e:
            raise ValidationError(f"Invalid end_date: {str(e)}")
    
    # Ensure end_date is after start_date
    if start_dt and end_dt and end_dt < start_dt:
        raise ValidationError("end_date must be after or equal to start_date")
    
    # Check date range limit
    if start_dt and end_dt:
        days_diff = (end_dt - start_dt).days
        if days_diff > max_days:
            raise ValidationError(
                f"Date range exceeds maximum of {max_days} days. "
                f"Requested: {days_diff} days"
            )
        if days_diff < 0:
            raise ValidationError("Invalid date range: start_date is after end_date")
    
    # Default to last 30 days if both are None
    if not start_dt and not end_dt:
        end_dt = timezone.now()
        start_dt = end_dt - timedelta(days=30)
    
    # Default end_date to now if only start_date provided
    if start_dt and not end_dt:
        end_dt = timezone.now()
        if (end_dt - start_dt).days > max_days:
            start_dt = end_dt - timedelta(days=max_days)
    
    # Default start_date if only end_date provided
    if end_dt and not start_dt:
        start_dt = end_dt - timedelta(days=min(30, max_days))
    
    return start_dt, end_dt


def validate_uuid_list(uuid_strings: list, param_name: str = "IDs") -> list:
    """
    Validate a list of UUID strings.
    
    Args:
        uuid_strings: List of UUID strings to validate
        param_name: Name of parameter for error messages
        
    Returns:
        List of validated UUID strings
        
    Raises:
        ValidationError: If any UUID is invalid
    """
    if not isinstance(uuid_strings, list):
        raise ValidationError(f"{param_name} must be a list")
    
    if len(uuid_strings) > 100:  # Prevent abuse
        raise ValidationError(f"{param_name} list cannot exceed 100 items")
    
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    validated = []
    for uuid_str in uuid_strings:
        if not isinstance(uuid_str, str):
            raise ValidationError(f"{param_name} must contain only string UUIDs")
        if not uuid_pattern.match(uuid_str):
            raise ValidationError(f"Invalid UUID format in {param_name}: {uuid_str}")
        validated.append(uuid_str)
    
    return validated


def validate_pagination(page: Optional[int], page_size: Optional[int]) -> Tuple[int, int]:
    """
    Validate pagination parameters.
    
    Args:
        page: Page number (1-based)
        page_size: Number of items per page
        
    Returns:
        Tuple of (validated_page, validated_page_size)
        
    Raises:
        ValidationError: If pagination parameters are invalid
    """
    if page is not None:
        if not isinstance(page, int) or page < 1:
            raise ValidationError("page must be a positive integer")
        if page > 10000:  # Prevent abuse
            raise ValidationError("page cannot exceed 10000")
    
    if page_size is not None:
        if not isinstance(page_size, int) or page_size < 1:
            raise ValidationError("page_size must be a positive integer")
        if page_size > 1000:  # Prevent abuse
            raise ValidationError("page_size cannot exceed 1000")
    
    validated_page = page if page is not None else 1
    validated_page_size = page_size if page_size is not None else 50
    
    return validated_page, validated_page_size


def validate_period(period: Optional[str]) -> str:
    """
    Validate time period parameter.
    
    Args:
        period: Period string ('day', 'week', 'month', 'year')
        
    Returns:
        Validated period string
        
    Raises:
        ValidationError: If period is invalid
    """
    valid_periods = ['day', 'week', 'month', 'year']
    
    if period is None:
        return 'day'
    
    if not isinstance(period, str):
        raise ValidationError("period must be a string")
    
    period_lower = period.lower()
    if period_lower not in valid_periods:
        raise ValidationError(
            f"Invalid period: {period}. Must be one of: {', '.join(valid_periods)}"
        )
    
    return period_lower


def sanitize_string(value: str, max_length: int = 255) -> str:
    """
    Sanitize string input to prevent injection.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
        
    Raises:
        ValidationError: If string exceeds max_length or contains dangerous characters
    """
    if not isinstance(value, str):
        raise ValidationError("Value must be a string")
    
    if len(value) > max_length:
        raise ValidationError(f"String exceeds maximum length of {max_length}")
    
    # Remove null bytes and control characters (except whitespace)
    sanitized = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
    
    return sanitized
