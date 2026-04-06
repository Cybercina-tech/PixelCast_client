"""
Content Storage Manager for PixelCast Signage Digital Signage System.

Provides secure, production-ready file storage for Content objects.
Supports both Local File System and Amazon S3 with automatic fallback.
Includes security features: file validation, hash-based integrity checking,
signed URLs, and access control.
"""

import os
import hashlib
import logging
from typing import Optional, Tuple, BinaryIO
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Custom exception for storage-related errors."""
    pass


class ContentStorageManager:
    """
    Manages content file storage with support for Local and S3 backends.
    
    Features:
    - Automatic backend selection (S3 or Local)
    - File type and size validation
    - Hash-based integrity checking
    - Secure signed URLs for S3
    - Access control and logging
    """
    
    @staticmethod
    def _get_storage_backend():
        """Get the configured storage backend."""
        return default_storage
    
    @staticmethod
    def _validate_file_type(file_obj: UploadedFile, content_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file type based on content type.
        
        Args:
            file_obj: Uploaded file object
            content_type: Expected content type (image, video, webview, etc.)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not hasattr(file_obj, 'content_type'):
            # If content_type not available, try to infer from extension
            filename = file_obj.name if hasattr(file_obj, 'name') else ''
            if not filename:
                return False, "Cannot determine file type"
        
        content_storage = getattr(settings, 'CONTENT_STORAGE', {})
        mime_type = getattr(file_obj, 'content_type', '')
        
        if content_type == 'image':
            allowed_types = content_storage.get('ALLOWED_IMAGE_TYPES', [])
            if mime_type and mime_type not in allowed_types:
                return False, f"Invalid image type: {mime_type}. Allowed: {allowed_types}"
        
        elif content_type == 'video':
            allowed_types = content_storage.get('ALLOWED_VIDEO_TYPES', [])
            if mime_type and mime_type not in allowed_types:
                return False, f"Invalid video type: {mime_type}. Allowed: {allowed_types}"
        
        elif content_type == 'webview':
            allowed_types = content_storage.get('ALLOWED_WEBVIEW_TYPES', [])
            if mime_type and mime_type not in allowed_types:
                return False, f"Invalid webview type: {mime_type}. Allowed: {allowed_types}"
        
        return True, None
    
    @staticmethod
    def _validate_file_size(file_obj: UploadedFile) -> Tuple[bool, Optional[str]]:
        """
        Validate file size.
        
        Args:
            file_obj: Uploaded file object
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        content_storage = getattr(settings, 'CONTENT_STORAGE', {})
        max_size = content_storage.get('MAX_FILE_SIZE', 5 * 1024 * 1024 * 1024)  # 5 GB default
        
        if hasattr(file_obj, 'size'):
            if file_obj.size > max_size:
                max_size_mb = max_size / (1024 * 1024)
                return False, f"File size ({file_obj.size / (1024 * 1024):.2f} MB) exceeds maximum allowed size ({max_size_mb} MB)"
        
        return True, None
    
    @staticmethod
    def _calculate_hash(file_obj: BinaryIO, algorithm: str = 'sha256') -> str:
        """
        Calculate hash of file content for integrity checking.
        
        Args:
            file_obj: File object to hash
            algorithm: Hash algorithm (default: sha256)
            
        Returns:
            Hexadecimal hash string
        """
        hash_obj = hashlib.new(algorithm)
        
        # Reset file pointer to beginning
        file_obj.seek(0)
        
        # Read file in chunks to handle large files
        chunk_size = 8192
        while chunk := file_obj.read(chunk_size):
            hash_obj.update(chunk)
        
        # Reset file pointer again
        file_obj.seek(0)
        
        return hash_obj.hexdigest()
    
    @staticmethod
    def _generate_storage_path(content_instance, user=None) -> str:
        """
        Generate storage path for content file with user-based organization.
        
        Path format: users/user_{user_id}/{type}/{type}_{uuid}.{ext}
        
        Args:
            content_instance: Content model instance
            user: User who uploaded the file (optional, will try to infer from content)
            
        Returns:
            Storage path string (normalized, no leading/trailing slashes)
        """
        # Get user ID - priority: provided user > content widget layer template created_by
        user_id = None
        if user and hasattr(user, 'id'):
            user_id = user.id
        else:
            # Try to get user from content relationships
            try:
                widget = content_instance.widget
                if widget:
                    layer = widget.layer
                    if layer:
                        template = layer.template
                        if template and hasattr(template, 'created_by') and template.created_by:
                            user_id = template.created_by.id
            except (AttributeError, Exception) as e:
                logger.warning(f"Could not determine user from content relationships: {e}")
        
        # Fallback to 'unknown' if no user found
        if not user_id:
            logger.warning(f"Content {content_instance.id} has no associated user, using 'unknown'")
            user_id = 'unknown'
        
        # Ensure user_id is a string
        user_id = str(user_id)
        
        # Get content type directory name
        content_type = content_instance.type.lower()
        type_dir_map = {
            'image': 'images',
            'video': 'videos',
            'text': 'texts',
            'webview': 'other',
            'chart': 'other',
            'json': 'other',
            'other': 'other'
        }
        type_dir = type_dir_map.get(content_type, 'other')
        
        # Generate filename: {type}_{uuid}.{ext}
        content_id = str(content_instance.id)
        
        # Get file extension
        ext = ''
        if hasattr(content_instance, '_uploaded_file_name'):
            filename = content_instance._uploaded_file_name
            # Extract extension from filename
            _, ext = os.path.splitext(filename)
            if not ext or ext == '.':
                ext = ContentStorageManager._get_file_extension(content_instance.type)
        else:
            ext = ContentStorageManager._get_file_extension(content_instance.type)
        
        # Ensure extension starts with dot
        if ext and not ext.startswith('.'):
            ext = '.' + ext
        
        # Generate new filename with UUID
        filename = f"{content_type}_{content_id}{ext}"
        
        # Sanitize filename (remove any path separators and invalid characters)
        filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_', '.'))
        
        # Build path: users/user_{user_id}/{type}/{filename}
        # Use os.path.join for cross-platform compatibility, then normalize
        path = os.path.join('users', f'user_{user_id}', type_dir, filename)
        
        # Normalize path separators (use forward slashes for consistency)
        path = path.replace('\\', '/')
        
        # Remove any leading/trailing slashes
        path = path.strip('/')
        
        logger.debug(f"Generated storage path: {path} for content {content_instance.id}")
        
        return path
    
    @staticmethod
    def _get_file_extension(content_type: str) -> str:
        """Get default file extension for content type."""
        extensions = {
            'image': '.jpg',
            'video': '.mp4',
            'webview': '.html',
            'text': '.txt',
            'json': '.json',
        }
        return extensions.get(content_type, '')
    
    @classmethod
    def save_content(cls, content_instance, file_obj: UploadedFile, user=None) -> Tuple[str, dict]:
        """
        Save content file to storage backend with comprehensive validation.
        
        Args:
            content_instance: Content model instance
            file_obj: Uploaded file object
            user: User who uploaded the file (for logging)
            
        Returns:
            Tuple of (storage_path, metadata_dict)
            
        Raises:
            StorageError: If validation or save fails
        """
        try:
            # Use comprehensive content validator
            try:
                from content_validation.validators import ContentValidator, ValidationError, SecurityValidationError
                from content_validation.utils import log_validation
                
                # Get filename
                filename = file_obj.name if hasattr(file_obj, 'name') else 'unknown'
                
                # Comprehensive validation
                validation_result = ContentValidator.validate_content(
                    file_obj=file_obj,
                    content_type=content_instance.type,
                    filename=filename
                )
                
                # Use sanitized filename
                sanitized_filename = validation_result.get('sanitized_filename', filename)
                
                # Log validation
                if user:
                    log_validation(
                        user_id=user.id if hasattr(user, 'id') else None,
                        username=user.username if hasattr(user, 'username') else 'unknown',
                        filename=filename,
                        sanitized_filename=sanitized_filename,
                        content_type=content_instance.type,
                        validation_result=validation_result
                    )
                
                # Merge validation metadata
                metadata_from_validation = validation_result.get('metadata', {})
                
            except ImportError:
                # Fallback to basic validation if content_validation not available
                logger.warning("content_validation module not available, using basic validation")
                
                # Basic validation
                is_valid, error = cls._validate_file_type(file_obj, content_instance.type)
                if not is_valid:
                    raise StorageError(error)
                
                is_valid, error = cls._validate_file_size(file_obj)
                if not is_valid:
                    raise StorageError(error)
                
                metadata_from_validation = {}
                sanitized_filename = file_obj.name if hasattr(file_obj, 'name') else 'unknown'
            
            except (ValidationError, SecurityValidationError) as e:
                # Log validation failure
                if user:
                    try:
                        from content_validation.utils import log_validation
                        log_validation(
                            user_id=user.id if hasattr(user, 'id') else None,
                            username=user.username if hasattr(user, 'username') else 'unknown',
                            filename=filename,
                            sanitized_filename=filename,
                            content_type=content_instance.type,
                            validation_result={
                                'is_valid': False,
                                'errors': [str(e)],
                                'warnings': [],
                                'metadata': {},
                                'sanitized_filename': filename
                            }
                        )
                    except:
                        pass
                
                raise StorageError(f"Validation failed: {str(e)}")
            
            # Calculate hash for integrity checking
            content_storage = getattr(settings, 'CONTENT_STORAGE', {})
            enable_hash = content_storage.get('ENABLE_HASH_VALIDATION', True)
            hash_algorithm = content_storage.get('HASH_ALGORITHM', 'sha256')
            
            file_hash = None
            if enable_hash:
                file_hash = cls._calculate_hash(file_obj, hash_algorithm)
            
            # Use file hash from validation if available
            if metadata_from_validation.get('file_hash'):
                file_hash = metadata_from_validation['file_hash']
            
            # Generate storage path with sanitized filename and user
            storage_path = cls._generate_storage_path(content_instance, user)
            logger.info(f"Generated storage path: {storage_path}")
            
            # Store sanitized filename for later use
            content_instance._uploaded_file_name = sanitized_filename
            
            # Ensure directory exists before saving
            storage = cls._get_storage_backend()
            directory = os.path.dirname(storage_path)
            
            logger.info(f"Storage backend: {type(storage).__name__}")
            logger.info(f"Directory to create: {directory}")
            
            # For local storage, create directories if they don't exist
            if hasattr(storage, 'location'):
                # Local file storage - create directory structure
                full_path = os.path.join(storage.location, directory)
                logger.info(f"Full directory path: {full_path}")
                
                try:
                    os.makedirs(full_path, exist_ok=True)
                    logger.info(f"Directory created/verified: {full_path}")
                    
                    # Verify directory is writable
                    if not os.access(full_path, os.W_OK):
                        logger.error(f"Directory is not writable: {full_path}")
                        raise StorageError(f"Storage directory is not writable: {full_path}")
                except OSError as e:
                    logger.error(f"Failed to create directory {full_path}: {e}", exc_info=True)
                    raise StorageError(f"Failed to create storage directory: {e}")
            # For S3 or other storage - directories are implicit, no need to create
            
            # Save file to storage backend
            storage = cls._get_storage_backend()
            
            # Read file content
            file_obj.seek(0)
            file_content = file_obj.read()
            file_size = len(file_content)
            
            logger.info(f"File content read: {file_size} bytes")
            logger.info(f"Saving to storage path: {storage_path}")
            
            # Save to storage
            try:
                # CRITICAL: Normalize path for Windows compatibility
                # Django's FileSystemStorage validates paths are within MEDIA_ROOT
                # On Windows, mixed slashes can cause "outside base directory" errors
                # Normalize both the storage_path and ensure MEDIA_ROOT is normalized
                if hasattr(storage, 'location'):
                    # Local storage - normalize paths
                    # Note: os is already imported at the top of the file
                    # Normalize storage_path to use forward slashes (Django expects this)
                    storage_path_normalized = storage_path.replace('\\', '/')
                    # Ensure no leading/trailing slashes
                    storage_path_normalized = storage_path_normalized.strip('/')
                    
                    # Get MEDIA_ROOT and normalize it
                    media_root = getattr(settings, 'MEDIA_ROOT', None)
                    if media_root:
                        # Convert Path object to string if needed
                        if hasattr(media_root, '__str__'):
                            media_root = str(media_root)
                        # Normalize MEDIA_ROOT path
                        media_root_normalized = os.path.normpath(media_root)
                        # Convert to absolute path
                        media_root_absolute = os.path.abspath(media_root_normalized)
                        
                        # Construct full path and normalize
                        full_path = os.path.join(media_root_absolute, storage_path_normalized)
                        full_path_normalized = os.path.normpath(full_path)
                        
                        # Verify path is within MEDIA_ROOT (security check)
                        if not full_path_normalized.startswith(media_root_absolute):
                            error_msg = f"Path integrity check failed: {full_path_normalized} is outside base directory {media_root_absolute}"
                            logger.error(error_msg)
                            raise StorageError(error_msg)
                        
                        logger.debug(f"Path normalized: {storage_path} -> {storage_path_normalized}")
                        logger.debug(f"MEDIA_ROOT: {media_root_absolute}")
                        logger.debug(f"Full path: {full_path_normalized}")
                    
                    # Use normalized path for storage.save()
                    saved_path = storage.save(storage_path_normalized, ContentFile(file_content))
                else:
                    # S3 or other storage - use path as-is
                    saved_path = storage.save(storage_path, ContentFile(file_content))
                
                logger.info(f"File saved successfully to: {saved_path}")
            except Exception as e:
                logger.error(f"Failed to save file to storage: {e}", exc_info=True)
                raise StorageError(f"Failed to save file to storage: {e}")
            
            # Get file URL - ensure consistent, reliable URL generation
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            
            if hasattr(storage, 'location'):
                # Local storage - construct proper media URL
                # saved_path from storage.save() is relative to MEDIA_ROOT
                # Normalize the path to ensure consistency
                clean_path = saved_path.replace('\\', '/').strip('/')
                
                # Ensure media_url ends with / and clean_path doesn't start with /
                media_url_clean = media_url.rstrip('/') + '/'
                if clean_path.startswith('/'):
                    clean_path = clean_path.lstrip('/')
                
                # Construct file_url: /media/path/to/file
                file_url = media_url_clean + clean_path
                # Collapse accidental duplicate slashes in path only (never strip "//" from https://)
                if not (file_url.startswith('http://') or file_url.startswith('https://')):
                    while '//' in file_url:
                        file_url = file_url.replace('//', '/')
                if not file_url.startswith('http') and not file_url.startswith('/'):
                    file_url = '/' + file_url
                
                logger.debug(f"Generated file_url for local storage: {file_url}")
            else:
                # S3 or other storage backend
                if hasattr(storage, 'url'):
                    try:
                        file_url = storage.url(saved_path)
                        # If storage.url returns a relative path, make it absolute
                        if file_url and not file_url.startswith('http'):
                            # It's a relative path, prepend media_url
                            clean_path = file_url.lstrip('/')
                            file_url = media_url.rstrip('/') + '/' + clean_path
                    except Exception as e:
                        logger.warning(f"Error getting URL from storage: {e}, using saved_path")
                        file_url = saved_path
                else:
                    # Fallback: use saved_path as-is
                    file_url = saved_path
                
                logger.debug(f"Generated file_url for remote storage: {file_url}")
            
            # Prepare metadata (merge with validation metadata)
            metadata = {
                'storage_path': saved_path,
                'file_url': file_url,
                'file_size': file_size,
                'file_hash': file_hash,
                'hash_algorithm': hash_algorithm if file_hash else None,
                'content_type': metadata_from_validation.get('mime_type') or getattr(file_obj, 'content_type', ''),
                'saved_at': timezone.now().isoformat(),
                'sanitized_filename': sanitized_filename,
                **{k: v for k, v in metadata_from_validation.items() if k not in ['file_size', 'file_hash', 'mime_type']}
            }
            
            logger.info(f"Content file saved: {saved_path} (size: {file_size} bytes, hash: {file_hash})")
            
            return saved_path, metadata
            
        except Exception as e:
            logger.error(f"Error saving content file: {str(e)}")
            raise StorageError(f"Failed to save content file: {str(e)}")
    
    @classmethod
    def get_content_url(cls, content_instance, expiration: Optional[int] = None) -> str:
        """
        Get secure URL for content file.
        
        For S3: Returns signed URL with expiration
        For Local: Returns media URL (absolute or relative based on context)
        
        Args:
            content_instance: Content model instance
            expiration: URL expiration time in seconds (for S3 signed URLs)
            
        Returns:
            URL string (reliable and consistent)
        """
        if not content_instance.file_url:
            raise StorageError("Content has no file_url")
        
        storage = cls._get_storage_backend()
        file_url = content_instance.file_url
        
        # Check if using S3 storage
        if hasattr(storage, 'url') and 's3' in str(type(storage)).lower():
            # For S3, generate signed URL
            content_storage = getattr(settings, 'CONTENT_STORAGE', {})
            default_expiration = content_storage.get('SIGNED_URL_EXPIRATION', 3600)
            expiration = expiration or default_expiration
            
            try:
                # Extract key from file_url or use storage_path
                if hasattr(content_instance, '_storage_path') and content_instance._storage_path:
                    key = content_instance._storage_path
                elif hasattr(content_instance, 'storage_path') and content_instance.storage_path:
                    key = content_instance.storage_path
                else:
                    # Try to extract from URL
                    if '.com/' in file_url:
                        key = file_url.split('.com/')[-1]
                    elif file_url.startswith('/'):
                        key = file_url.lstrip('/')
                    else:
                        key = file_url
                
                # For boto3, generate presigned URL
                if hasattr(storage, 'connection'):
                    # This is S3Boto3Storage
                    try:
                        import boto3
                        from botocore.client import Config
                        
                        s3_client = boto3.client(
                            's3',
                            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                            region_name=settings.AWS_S3_REGION_NAME,
                            config=Config(signature_version='s3v4')
                        )
                        
                        signed_url = s3_client.generate_presigned_url(
                            'get_object',
                            Params={
                                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                'Key': key
                            },
                            ExpiresIn=expiration
                        )
                        logger.debug(f"Generated S3 signed URL for key: {key}")
                        return signed_url
                    except ImportError:
                        logger.warning("boto3 not installed, cannot generate signed URLs for S3")
                    except Exception as e:
                        logger.error(f"Error generating S3 signed URL: {e}", exc_info=True)
                
                # Fallback: use storage.url() method
                try:
                    signed_url = storage.url(key)
                    if signed_url:
                        return signed_url
                except Exception as e:
                    logger.warning(f"Error getting URL from storage: {e}")
                
                # Final fallback: return original file_url
                return file_url
                
            except Exception as e:
                logger.error(f"Error generating signed URL: {str(e)}", exc_info=True)
                # Fallback to regular URL
                return file_url
        
        # For local storage, return consistent media URL
        # If file_url is already a full HTTP(S) URL, return it as-is
        if file_url.startswith('http://') or file_url.startswith('https://'):
            return file_url
        
        # Normalize the file_url path
        clean_path = file_url.replace('\\', '/').strip('/')
        
        # If it's already a proper media URL path, return it
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        media_url_clean = media_url.rstrip('/')
        
        # If file_url already starts with media_url, return as-is (normalized)
        if clean_path.startswith(media_url_clean.lstrip('/')):
            # Ensure it starts with /
            if not clean_path.startswith('/'):
                clean_path = '/' + clean_path
            return clean_path
        
        # Construct proper media URL
        # Ensure media_url ends with / and clean_path doesn't start with /
        if clean_path.startswith('/'):
            clean_path = clean_path.lstrip('/')
        
        result_url = f"{media_url_clean}/{clean_path}"
        if not (result_url.startswith('http://') or result_url.startswith('https://')):
            while '//' in result_url:
                result_url = result_url.replace('//', '/')
        if not result_url.startswith('http') and not result_url.startswith('/'):
            result_url = '/' + result_url
        
        logger.debug(f"Generated content URL: {result_url}")
        return result_url
    
    @classmethod
    def delete_content(cls, content_instance) -> bool:
        """
        Delete content file from storage.
        
        Args:
            content_instance: Content model instance
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not content_instance.file_url:
            return True  # Nothing to delete
        
        try:
            storage = cls._get_storage_backend()
            
            # Extract storage path
            if hasattr(content_instance, '_storage_path'):
                storage_path = content_instance._storage_path
            else:
                # Try to extract from file_url
                storage_path = content_instance.file_url
                # Remove domain/prefix if present
                if 'http' in storage_path:
                    # Extract path after domain
                    parts = storage_path.split('/')
                    # Find 'content' in path
                    try:
                        content_idx = parts.index('content')
                        storage_path = '/'.join(parts[content_idx:])
                    except ValueError:
                        pass
            
            # Delete file
            if storage.exists(storage_path):
                storage.delete(storage_path)
                logger.info(f"Content file deleted: {storage_path}")
                return True
            else:
                logger.warning(f"Content file not found for deletion: {storage_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting content file: {str(e)}")
            return False
    
    @classmethod
    def verify_content_integrity(cls, content_instance, file_obj: Optional[BinaryIO] = None) -> Tuple[bool, Optional[str]]:
        """
        Verify content file integrity using hash.
        
        Args:
            content_instance: Content model instance
            file_obj: Optional file object to verify (if not provided, reads from storage)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        content_storage = getattr(settings, 'CONTENT_STORAGE', {})
        enable_hash = content_storage.get('ENABLE_HASH_VALIDATION', True)
        
        if not enable_hash:
            return True, None
        
        if not hasattr(content_instance, 'file_hash') or not content_instance.file_hash:
            return True, None  # No hash to verify
        
        try:
            hash_algorithm = content_storage.get('HASH_ALGORITHM', 'sha256')
            
            if file_obj:
                # Calculate hash from provided file object
                calculated_hash = cls._calculate_hash(file_obj, hash_algorithm)
            else:
                # Read from storage and calculate hash
                storage = cls._get_storage_backend()
                
                # CRITICAL: Normalize file_url to get proper storage path
                # file_url might be absolute path (C:\media\users\...) or relative path
                file_url = content_instance.file_url
                if not file_url:
                    return False, "Content has no file_url"
                
                # Extract storage path from file_url
                # If file_url is absolute path, extract relative part
                # If file_url is relative path, use as-is
                storage_path = file_url
                
                # Normalize path: remove leading slashes and normalize separators
                storage_path = storage_path.replace('\\', '/').strip('/')
                
                # If path starts with MEDIA_URL, remove it
                media_url = getattr(settings, 'MEDIA_URL', '/media/')
                media_url_clean = media_url.rstrip('/').lstrip('/')
                if storage_path.startswith(media_url_clean):
                    storage_path = storage_path[len(media_url_clean):].lstrip('/')
                
                # If path is absolute (starts with drive letter on Windows or / on Unix)
                # Extract relative part from MEDIA_ROOT
                if os.path.isabs(storage_path) or (len(storage_path) > 1 and storage_path[1] == ':'):
                    # This is an absolute path, need to extract relative part
                    media_root = getattr(settings, 'MEDIA_ROOT', None)
                    if media_root:
                        # Convert Path object to string if needed
                        if hasattr(media_root, '__str__'):
                            media_root = str(media_root)
                        media_root_abs = os.path.abspath(os.path.normpath(media_root))
                        storage_path_abs = os.path.abspath(os.path.normpath(storage_path))
                        
                        # Check if storage_path is within MEDIA_ROOT
                        if not storage_path_abs.startswith(media_root_abs):
                            error_msg = f"Path integrity check failed: {storage_path_abs} is outside base directory {media_root_abs}"
                            logger.error(error_msg)
                            return False, error_msg
                        
                        # Extract relative path
                        try:
                            storage_path = os.path.relpath(storage_path_abs, media_root_abs)
                            # Normalize to forward slashes for Django
                            storage_path = storage_path.replace('\\', '/')
                        except ValueError:
                            # Paths are on different drives (Windows)
                            error_msg = f"Cannot extract relative path from absolute path: {storage_path}"
                            logger.error(error_msg)
                            return False, error_msg
                
                # Final normalization: ensure no leading/trailing slashes
                storage_path = storage_path.strip('/')
                
                # Verify path is safe (no directory traversal)
                if '..' in storage_path or storage_path.startswith('/'):
                    error_msg = f"Invalid storage path detected: {storage_path}"
                    logger.error(error_msg)
                    return False, error_msg
                
                logger.debug(f"Normalized storage path: {file_url} -> {storage_path}")
                
                # Try to open file - handle various path formats
                # Try normalized path first
                file_path = None
                if storage.exists(storage_path):
                    file_path = storage_path
                else:
                    # Try alternative path formats
                    # Sometimes file_url might be stored differently
                    # Try with leading slash
                    alt_path = '/' + storage_path if not storage_path.startswith('/') else storage_path
                    if storage.exists(alt_path):
                        file_path = alt_path
                    else:
                        # Try original file_url as fallback (if it's a relative path)
                        if not os.path.isabs(file_url) and storage.exists(file_url):
                            file_path = file_url
                        else:
                            return False, f"File not found in storage. Tried paths: {storage_path}, {alt_path}, {file_url}"
                
                # Open file and calculate hash
                try:
                    with storage.open(file_path, 'rb') as f:
                        calculated_hash = cls._calculate_hash(f, hash_algorithm)
                except Exception as e:
                    error_msg = f"Cannot open file from storage: {str(e)}. Path: {file_path}"
                    logger.error(error_msg)
                    return False, error_msg
            
            # Compare hashes
            stored_hash = content_instance.file_hash
            if calculated_hash.lower() != stored_hash.lower():
                return False, f"Hash mismatch: stored={stored_hash}, calculated={calculated_hash}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error verifying content integrity: {str(e)}", exc_info=True)
            return False, f"Integrity check failed: {str(e)}"
    
    @staticmethod
    def verify_user_access(content_instance, user) -> bool:
        """
        Verify that a user has access to a content file.
        
        Args:
            content_instance: Content model instance
            user: User to check access for
            
        Returns:
            True if user has access, False otherwise
        """
        if not user or not hasattr(user, 'id'):
            return False
        
        # Get user from content relationships
        try:
            widget = content_instance.widget
            if widget:
                layer = widget.layer
                if layer:
                    template = layer.template
                    if template:
                        # Check if user created the template
                        if hasattr(template, 'created_by') and template.created_by:
                            if template.created_by.id == user.id:
                                return True
                        
                        # Check if user has view permission via RolePermissions
                        try:
                            from accounts.permissions import RolePermissions
                            return RolePermissions.can_view_resource(user, template)
                        except:
                            pass
        except (AttributeError, Exception) as e:
            logger.warning(f"Error checking user access for content {content_instance.id}: {e}")
        
        return False
    
    @classmethod
    def list_contents(cls, screen_id=None, template_id=None, limit=100, offset=0):
        """
        List content files with optional filtering.
        
        Args:
            screen_id: Optional screen ID to filter by
            template_id: Optional template ID to filter by
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of content metadata dictionaries
        """
        from .models import Content
        
        queryset = Content.objects.filter(is_active=True)
        
        if screen_id:
            # Filter by screens that have this content's template
            queryset = queryset.filter(
                widget__layer__template__screens__id=screen_id
            )
        
        if template_id:
            queryset = queryset.filter(
                widget__layer__template__id=template_id
            )
        
        queryset = queryset.select_related('widget__layer__template')[offset:offset+limit]
        
        results = []
        for content in queryset:
            results.append({
                'id': str(content.id),
                'name': content.name,
                'type': content.type,
                'file_url': content.file_url,
                'file_size': getattr(content, 'file_size', None),
                'download_status': content.download_status,
                'created_at': content.created_at.isoformat(),
            })
        
        return results

