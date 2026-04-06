"""
Utility functions for setup/installation process.
"""
import os
import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)


def _env_declares_installed():
    """
    True if PIXELCAST_SIGNAGE_INSTALLED (or legacy SCREENGRAM_INSTALLED) is set in .env.
    Truthy strings match settings.env(..., cast=bool): true, 1, yes, on.
    """
    raw = (
        os.environ.get('PIXELCAST_SIGNAGE_INSTALLED', '').strip()
        or os.environ.get('SCREENGRAM_INSTALLED', '').strip()
    ).lower()
    return raw in ('true', '1', 'yes', 'on')


def get_installed_lock_path():
    """Get the path to the installation lock file.
    
    Uses INSTALLATION_STATE_DIR (Docker volume mount) or BASE_DIR for local dev.
    """
    state_dir = getattr(settings, 'INSTALLATION_STATE_DIR', settings.BASE_DIR)
    return Path(state_dir) / 'installed.lock'


def is_installed():
    """
    Installation is complete if PIXELCAST_SIGNAGE_INSTALLED (or legacy SCREENGRAM_INSTALLED) is set in the environment (.env)
    or installed.lock exists under INSTALLATION_STATE_DIR.
    """
    if _env_declares_installed():
        return True
    lock_path = get_installed_lock_path()
    return lock_path.is_file()


def mark_as_installed():
    """
    Mark installation as completed by creating the installed.lock file.
    
    Returns:
        bool: True if lock file was created successfully, False otherwise
    """
    try:
        lock_path = get_installed_lock_path()
        parent = lock_path.parent
        # Ensure parent directory exists (required for Docker volume mount)
        parent.mkdir(parents=True, exist_ok=True)
        lock_path.touch()
        if lock_path.is_file():
            logger.info("Installation lock file created at %s", lock_path)
            return True
        logger.error("Lock file creation failed: path exists but is not a file: %s", lock_path)
        return False
    except PermissionError as e:
        logger.error("Permission denied creating installed.lock at %s: %s", lock_path, e)
        return False
    except Exception as e:
        logger.exception("Failed to create installed.lock: %s", e)
        return False


def reset_installation():
    """
    Reset installation by removing the lock file (for testing/debugging).
    
    Returns:
        bool: True if lock file was removed successfully, False otherwise
    """
    try:
        lock_path = get_installed_lock_path()
        if lock_path.exists():
            lock_path.unlink()
        return not lock_path.exists()
    except Exception:
        return False
