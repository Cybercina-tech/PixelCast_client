"""
Environment File Manager

Handles dynamic .env file creation and updates during installation.
"""
import os
import re
import logging
from pathlib import Path
from typing import Dict, Optional
from django.conf import settings

from setup.paths import resolve_env_file_paths

logger = logging.getLogger(__name__)


class EnvManagerError(Exception):
    """Custom exception for env manager errors."""
    pass


def escape_env_value(value: str) -> str:
    """
    Escape a value for use in .env file.
    
    Handles:
    - Quotes and special characters
    - Spaces (wraps in quotes if needed)
    - Newlines and other control characters
    
    Args:
        value: The value to escape
        
    Returns:
        Escaped value string
    """
    if not isinstance(value, str):
        value = str(value)
    
    # Remove leading/trailing whitespace
    value = value.strip()
    
    # If value contains spaces, quotes, or special characters, wrap in quotes
    if any(char in value for char in [' ', '"', "'", '$', '`', '\\', '\n', '\r', '\t']):
        # Escape backslashes and quotes
        value = value.replace('\\', '\\\\')
        value = value.replace('"', '\\"')
        # Wrap in double quotes
        value = f'"{value}"'
    
    return value


def parse_env_file(file_path: Path) -> Dict[str, str]:
    """
    Parse an existing .env file and return a dictionary of key-value pairs.
    
    Args:
        file_path: Path to the .env file
        
    Returns:
        Dictionary of environment variables
    """
    env_vars = {}
    
    if not file_path.exists() or file_path.is_dir():
        return env_vars
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE format
                # Handle quoted values and escaped characters
                match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$', line)
                if match:
                    key = match.group(1)
                    value = match.group(2).strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1].replace('\\"', '"').replace('\\\\', '\\')
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1].replace("\\'", "'").replace('\\\\', '\\')
                    
                    env_vars[key] = value
                else:
                    logger.warning(f"Could not parse line {line_num} in {file_path}: {line}")
    
    except (FileNotFoundError, IsADirectoryError, PermissionError):
        # Graceful fallback for wizard flows where /config/.env is optional
        # or mount timing causes a transient missing file.
        logger.info(f".env file not found while parsing: {file_path}. Continuing with empty env.")
        return {}
    except Exception as e:
        logger.error(f"Error parsing .env file {file_path}: {str(e)}")
        raise EnvManagerError(f"Failed to parse .env file: {str(e)}")
    
    return env_vars


def read_template_file(template_path: Path) -> Dict[str, str]:
    """
    Read environment variables from template file.
    
    Args:
        template_path: Path to .env.template file
        
    Returns:
        Dictionary of environment variables from template
    """
    if not template_path.exists():
        logger.info(f"Template file {template_path} does not exist. Using empty template.")
        return {}
    
    return parse_env_file(template_path)


def validate_env_data(data_dict: Dict[str, str]) -> tuple[bool, Optional[str]]:
    """
    Validate environment data before writing.
    Auto-fix: if DB_PASSWORD is missing or empty and DB_USER is provided, use DB_USER as DB_PASSWORD.
    
    Args:
        data_dict: Dictionary of environment variables to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not data_dict:
        return False, "No environment data provided"
    
    # Normalize: use DB_USER as DB_PASSWORD when password is missing/empty (username-as-password)
    data_dict = dict(data_dict)
    if (not data_dict.get('DB_PASSWORD') or not str(data_dict.get('DB_PASSWORD', '')).strip()) and data_dict.get('DB_USER'):
        data_dict['DB_PASSWORD'] = data_dict['DB_USER']
    
    # Required fields for basic functionality
    required_fields = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST']
    
    for field in required_fields:
        if field not in data_dict or not data_dict[field] or not str(data_dict[field]).strip():
            return False, f"Required field '{field}' is missing or empty"
    
    # Validate SECRET_KEY if provided
    if 'SECRET_KEY' in data_dict:
        secret_key = str(data_dict['SECRET_KEY']).strip()
        if len(secret_key) < 50:
            return False, "SECRET_KEY must be at least 50 characters long"
    
    return True, None


def check_write_permissions(directory: Path) -> tuple[bool, Optional[str]]:
    """
    Check if we have write permissions in the directory.
    
    Args:
        directory: Directory to check
        
    Returns:
        Tuple of (has_permission, error_message)
    """
    if not directory.exists():
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return False, f"Cannot create directory {directory}: {str(e)}"
    
    if not os.access(directory, os.W_OK):
        return False, f"No write permission in directory {directory}"
    
    # Try to create a test file
    test_file = directory / '.env_write_test'
    try:
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        return False, f"Cannot write to directory {directory}: {str(e)}"
    
    return True, None


def update_env_file(
    data_dict: Dict[str, str],
    env_file_path: Optional[Path] = None,
    template_path: Optional[Path] = None,
    preserve_existing: bool = True
) -> tuple[bool, Optional[str]]:
    """
    Update or create .env file with provided data.
    
    Merges new values with existing .env file and template, preserving
    manually added variables if preserve_existing is True.
    
    Args:
        data_dict: Dictionary of environment variables to set/update
        env_file_path: Path to .env file (defaults to project root)
        template_path: Path to .env.template file (defaults to project root)
        preserve_existing: If True, preserve existing variables not in data_dict
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        def _ensure_file_path(candidate: Path) -> Path:
            """
            Ensure the target path is a writable file path.
            If candidate points to a directory (common with broken bind mounts),
            fallback to BASE_DIR.parent/.env.
            """
            candidate = Path(candidate)
            if candidate.is_dir():
                fallback = Path(settings.BASE_DIR).parent / '.env'
                logger.warning(
                    f"Configured env path points to a directory ({candidate}); "
                    f"falling back to {fallback}"
                )
                return fallback
            return candidate

        # Determine file paths (same resolution as settings.load_dotenv)
        if env_file_path is None:
            env_file_path, _ = resolve_env_file_paths(Path(settings.BASE_DIR))
        else:
            env_file_path = Path(env_file_path)
        env_file_path = _ensure_file_path(env_file_path)

        if template_path is None:
            _, template_path = resolve_env_file_paths(Path(settings.BASE_DIR))
        else:
            template_path = Path(template_path)
        
        # Validate data
        is_valid, error_msg = validate_env_data(data_dict)
        if not is_valid:
            return False, error_msg
        
        # Check write permissions
        has_permission, error_msg = check_write_permissions(env_file_path.parent)
        if not has_permission:
            return False, error_msg
        
        # Auto-fix: use DB_USER as DB_PASSWORD when password is missing/empty (before merge)
        data_dict = dict(data_dict)
        if (not data_dict.get('DB_PASSWORD') or not str(data_dict.get('DB_PASSWORD', '')).strip()) and data_dict.get('DB_USER'):
            data_dict['DB_PASSWORD'] = data_dict['DB_USER']
        
        # Read existing .env file (if exists)
        existing_vars = {}
        if env_file_path.exists() and preserve_existing:
            existing_vars = parse_env_file(env_file_path)
            logger.info(f"Read {len(existing_vars)} existing variables from .env file")
        
        # Read template file (if exists)
        template_vars = read_template_file(template_path)
        if template_vars:
            logger.info(f"Read {len(template_vars)} variables from template file")
        
        # Merge: template -> existing -> new data (new data takes precedence)
        merged_vars = {}
        merged_vars.update(template_vars)
        if preserve_existing:
            merged_vars.update(existing_vars)
        merged_vars.update(data_dict)
        # Ensure POSTGRES_PASSWORD for Docker (same as DB_PASSWORD)
        if 'DB_PASSWORD' in merged_vars and 'POSTGRES_PASSWORD' not in merged_vars:
            merged_vars['POSTGRES_PASSWORD'] = merged_vars['DB_PASSWORD']
        
        # Write merged variables to .env file
        try:
            with open(env_file_path, 'w', encoding='utf-8') as f:
                # Write header comment
                f.write("# PixelCast Signage Environment Configuration\n")
                f.write("# Generated/Updated by Installation Wizard\n")
                f.write("# DO NOT EDIT MANUALLY - Use the installation wizard or update via env_manager.py\n\n")
                
                # Group variables by category (POSTGRES_PASSWORD = DB_PASSWORD for Docker)
                categories = {
                    'Django Settings': ['SECRET_KEY', 'DEBUG', 'ALLOWED_HOSTS'],
                    'Database Configuration': ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'POSTGRES_PASSWORD', 'DB_HOST', 'DB_PORT', 'USE_SQLITE'],
                    'Application URLs': ['BASE_URL'],
                    'Redis Configuration': ['REDIS_HOST', 'REDIS_PORT', 'USE_REDIS_CACHE', 'REDIS_CACHE_URL', 'REDIS_PASSWORD'],
                    'Celery Configuration': ['CELERY_BROKER_URL', 'CELERY_RESULT_BACKEND'],
                    'Channel Layers': ['CHANNEL_LAYERS_BACKEND'],
                    'Port Mappings': ['BACKEND_PORT', 'FRONTEND_HOST_PORT', 'HTTP_PORT'],
                }
                
                # Write categorized variables
                written_keys = set()
                for category, keys in categories.items():
                    category_vars = {k: v for k, v in merged_vars.items() if k in keys}
                    if category_vars:
                        f.write(f"# {category}\n")
                        for key in keys:
                            if key in merged_vars:
                                value = escape_env_value(str(merged_vars[key]))
                                f.write(f"{key}={value}\n")
                                written_keys.add(key)
                        f.write("\n")
                
                # Write remaining variables (not in categories)
                remaining_vars = {k: v for k, v in merged_vars.items() if k not in written_keys}
                if remaining_vars:
                    f.write("# Other Configuration\n")
                    for key, value in sorted(remaining_vars.items()):
                        escaped_value = escape_env_value(str(value))
                        f.write(f"{key}={escaped_value}\n")
                    f.write("\n")
            
            logger.info(f"Successfully wrote {len(merged_vars)} variables to {env_file_path}")
            return True, None
        
        except OSError as e:
            errno = getattr(e, 'errno', None)
            logger.error(
                f"Failed to write .env file: {type(e).__name__} errno={errno} path={env_file_path} detail={e!s}",
                exc_info=True
            )
            return False, f"Failed to write .env file: {e!s} (errno={errno})"
        except Exception as e:
            error_msg = f"Failed to write .env file: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    except EnvManagerError:
        raise
    except Exception as e:
        error_msg = f"Unexpected error updating .env file: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg


def finalize_installation(env_data: Dict[str, str]) -> tuple[bool, Optional[str]]:
    """
    Finalize installation by updating .env file and creating installed.lock.
    
    This is a convenience function that:
    1. Updates the .env file with provided data
    2. Creates the installed.lock file
    
    Args:
        env_data: Dictionary of environment variables to save
        
    Returns:
        Tuple of (success, error_message)
    """
    from .utils import mark_as_installed
    
    # Update .env file
    success, error_msg = update_env_file(env_data)
    if not success:
        return False, error_msg
    
    # Create installed.lock file
    if not mark_as_installed():
        return False, "Failed to create installed.lock file"
    
    logger.info("Installation finalized successfully")
    return True, None

