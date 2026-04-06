"""
Custom validators for user management.

Provides additional validation beyond Django's built-in validators.
"""
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _
import re

_email_validator = EmailValidator()


def validate_username_format(value):
    """
    Validate username format.

    If the value contains ``@``, treat it as email-as-username (signup uses email for ``username``)
    and validate with Django's email validator (Unicode, ``+``, etc.).
    Otherwise apply legacy ASCII username rules.
    """
    if not value:
        return

    value = value.strip()
    if len(value) < 3:
        raise ValidationError(_('Username must be at least 3 characters long.'))

    if len(value) > 150:
        raise ValidationError(_('Username is too long (maximum 150 characters).'))

    if '@' in value:
        try:
            _email_validator(value)
        except ValidationError as e:
            raise ValidationError(e.messages)
        return

    if value[0].isdigit():
        raise ValidationError(_('Username cannot start with a number.'))

    pattern = r'^[a-zA-Z][a-zA-Z0-9@.+_-]*$'
    if not re.match(pattern, value):
        raise ValidationError(_('Username can only contain letters, numbers, and @/./+/-/_ characters.'))


def validate_phone_number(value):
    """
    Validate phone number format.
    
    Accepts international format with optional + prefix.
    """
    if not value:
        return
    
    # Remove whitespace
    value = value.strip()
    
    # International format: + followed by digits, or digits only
    pattern = r'^\+?[1-9]\d{8,14}$'
    if not re.match(pattern, value):
        raise ValidationError(_('Phone number must be in international format (e.g., +1234567890).'))


def validate_organization_name(value):
    """
    Validate organization name format.
    
    Rules:
    - 2-255 characters
    - No special characters except spaces, hyphens, and underscores
    """
    if not value:
        return
    
    if len(value) < 2:
        raise ValidationError(_('Organization name must be at least 2 characters long.'))
    
    if len(value) > 255:
        raise ValidationError(_('Organization name is too long (maximum 255 characters).'))
    
    # Allowed: letters, numbers, spaces, hyphens, underscores
    pattern = r'^[a-zA-Z0-9\s_-]+$'
    if not re.match(pattern, value):
        raise ValidationError(_('Organization name can only contain letters, numbers, spaces, hyphens, and underscores.'))


def validate_email_domain(value):
    """
    Optional: Validate email domain (can be extended to whitelist/blacklist).
    """
    if not value:
        return
    
    # Extract domain
    if '@' not in value:
        return
    
    domain = value.split('@')[1].lower()
    
    # Block common disposable email domains
    disposable_domains = [
        'tempmail.com',
        'throwaway.email',
        'guerrillamail.com',
        '10minutemail.com',
    ]
    
    if domain in disposable_domains:
        raise ValidationError(_('Disposable email addresses are not allowed.'))
