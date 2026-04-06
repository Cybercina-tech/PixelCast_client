"""
Test-specific Django settings.
Used when running tests to ensure fast, isolated test execution.
"""
import os
import sys
import tempfile

# Add BackEnd directory to Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import base settings
try:
    from Screengram.settings import *
except ImportError:
    # Fallback if import fails
    import django
    from django.conf import settings as django_settings
    from django.test.utils import setup_test_environment
    setup_test_environment()
    django.setup()

# Use in-memory SQLite for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations during tests for speed
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Use faster password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# In-memory cache so CacheManager / RateLimiter tests work without Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'screengram-test-cache',
    }
}

# Disable email sending
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Use in-memory channel layer for tests
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# Disable Celery for tests (if available)
try:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
except:
    pass

# Test media root
MEDIA_ROOT = tempfile.mkdtemp()

# Disable logging during tests (optional, comment out if you want logs)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# Content storage settings for tests
CONTENT_STORAGE = {
    'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10 MB for tests
    'ALLOWED_IMAGE_TYPES': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    'ALLOWED_VIDEO_TYPES': ['video/mp4', 'video/webm'],
    'ALLOWED_WEBVIEW_TYPES': ['text/html'],
    'SIGNED_URL_EXPIRATION': 3600,
    'ENABLE_HASH_VALIDATION': True,
    'HASH_ALGORITHM': 'sha256',
}

# Disable S3 for tests (use local storage)
USE_S3_STORAGE = False

# Avoid license middleware blocking API tests that expect 201/401/403 from auth alone
LICENSE_ENFORCEMENT_ENABLED = False

# Tests use http://testserver; do not redirect to HTTPS (BASE_URL may be https in developer .env)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
