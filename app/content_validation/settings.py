"""
Content validation settings and configuration.

Can be extended in Django settings.py
"""
from django.conf import settings

# Content validation settings
CONTENT_VALIDATION_SETTINGS = {
    # Maximum files per bulk validation
    'MAX_BULK_FILES': getattr(settings, 'CONTENT_VALIDATION_MAX_BULK_FILES', 100),
    
    # Enable virus/malware scanning (requires external service integration)
    'ENABLE_VIRUS_SCAN': getattr(settings, 'CONTENT_VALIDATION_ENABLE_VIRUS_SCAN', False),
    
    # Virus scanning service URL (if enabled)
    'VIRUS_SCAN_API_URL': getattr(settings, 'CONTENT_VALIDATION_VIRUS_SCAN_API_URL', None),
    
    # Virus scanning API key (if required)
    'VIRUS_SCAN_API_KEY': getattr(settings, 'CONTENT_VALIDATION_VIRUS_SCAN_API_KEY', None),
    
    # Enable detailed logging
    'ENABLE_DETAILED_LOGGING': getattr(settings, 'CONTENT_VALIDATION_ENABLE_DETAILED_LOGGING', True),
    
    # Strict mode: reject files with warnings
    'STRICT_MODE': getattr(settings, 'CONTENT_VALIDATION_STRICT_MODE', False),
}
