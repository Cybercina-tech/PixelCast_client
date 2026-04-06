"""
Bulk content validation utilities.

Supports validating multiple files in one request with detailed per-file results.
"""
import logging
from typing import List, Dict, Any, Tuple
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone

from .validators import ContentValidator, ValidationError, SecurityValidationError

logger = logging.getLogger(__name__)


class BulkValidationResult:
    """
    Result for a single file in bulk validation.
    """
    def __init__(self, filename: str):
        self.filename = filename
        self.is_valid = False
        self.errors = []
        self.warnings = []
        self.metadata = {}
        self.sanitized_filename = filename
    
    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            'filename': self.filename,
            'sanitized_filename': self.sanitized_filename,
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'metadata': self.metadata
        }


class BulkValidator:
    """
    Validates multiple content files in bulk.
    """
    
    @classmethod
    def validate_files(
        cls,
        files: List[Tuple[UploadedFile, str, str]],  # (file_obj, content_type, filename)
        max_files: int = 100
    ) -> Dict[str, Any]:
        """
        Validate multiple files.
        
        Args:
            files: List of tuples (file_obj, content_type, filename)
            max_files: Maximum number of files allowed per batch
            
        Returns:
            Dict with validation results:
            {
                'total_count': int,
                'valid_count': int,
                'invalid_count': int,
                'results': List[BulkValidationResult]
            }
        """
        if len(files) > max_files:
            raise ValidationError(f"Too many files. Maximum {max_files} files allowed per batch, got {len(files)}")
        
        results = []
        valid_count = 0
        invalid_count = 0
        
        for file_obj, content_type, filename in files:
            result = BulkValidationResult(filename)
            
            try:
                validation_result = ContentValidator.validate_content(
                    file_obj=file_obj,
                    content_type=content_type,
                    filename=filename
                )
                
                result.is_valid = validation_result['is_valid']
                result.errors = validation_result.get('errors', [])
                result.warnings = validation_result.get('warnings', [])
                result.metadata = validation_result.get('metadata', {})
                result.sanitized_filename = validation_result.get('sanitized_filename', filename)
                
                if result.is_valid:
                    valid_count += 1
                else:
                    invalid_count += 1
                    
            except SecurityValidationError as e:
                result.is_valid = False
                result.errors.append(f"Security validation failed: {str(e)}")
                invalid_count += 1
                logger.warning(f"Security validation failed for {filename}: {str(e)}")
                
            except ValidationError as e:
                result.is_valid = False
                result.errors.append(str(e))
                invalid_count += 1
                logger.warning(f"Validation failed for {filename}: {str(e)}")
                
            except Exception as e:
                result.is_valid = False
                result.errors.append(f"Unexpected validation error: {str(e)}")
                invalid_count += 1
                logger.error(f"Unexpected error validating {filename}: {str(e)}")
            
            results.append(result)
        
        return {
            'total_count': len(files),
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'results': [r.to_dict() for r in results]
        }
    
    @classmethod
    def validate_and_filter_valid_files(
        cls,
        files: List[Tuple[UploadedFile, str, str]]
    ) -> Tuple[List[Tuple[UploadedFile, str, str]], Dict[str, Any]]:
        """
        Validate files and return only valid ones along with results.
        
        Args:
            files: List of tuples (file_obj, content_type, filename)
            
        Returns:
            Tuple of (valid_files, validation_results_dict)
        """
        validation_results = cls.validate_files(files)
        
        # Filter valid files
        valid_files = []
        for i, result_dict in enumerate(validation_results['results']):
            if result_dict['is_valid']:
                valid_files.append(files[i])
        
        return valid_files, validation_results
