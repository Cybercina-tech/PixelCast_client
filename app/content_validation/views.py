"""
Content validation API views.

Provides endpoints for validating content before upload and bulk validation.
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.uploadedfile import UploadedFile

from .validators import ContentValidator, ValidationError, SecurityValidationError
from .bulk_validator import BulkValidator
from .utils import log_validation

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_content(request):
    """
    POST /api/content-validation/validate/
    Validate a single content file before upload.
    
    Request:
    - file: Uploaded file
    - content_type: Expected content type (image, video, text, json, webview)
    - filename: Optional filename override
    
    Response:
    {
        "is_valid": bool,
        "errors": List[str],
        "warnings": List[str],
        "metadata": Dict,
        "sanitized_filename": str
    }
    """
    if 'file' not in request.FILES:
        return Response(
            {'error': 'File is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    file_obj = request.FILES['file']
    content_type = request.data.get('content_type', '')
    filename = request.data.get('filename') or file_obj.name
    
    if not content_type:
        return Response(
            {'error': 'content_type is required (image, video, text, json, webview)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if content_type not in ['image', 'video', 'text', 'json', 'webview']:
        return Response(
            {'error': f'Invalid content_type: {content_type}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = request.user
    
    try:
        # Validate content
        validation_result = ContentValidator.validate_content(
            file_obj=file_obj,
            content_type=content_type,
            filename=filename
        )
        
        # Log validation
        log_validation(
            user_id=user.id,
            username=user.username,
            filename=filename,
            sanitized_filename=validation_result.get('sanitized_filename', filename),
            content_type=content_type,
            validation_result=validation_result
        )
        
        return Response({
            'status': 'success',
            'is_valid': validation_result['is_valid'],
            'errors': validation_result.get('errors', []),
            'warnings': validation_result.get('warnings', []),
            'metadata': validation_result.get('metadata', {}),
            'sanitized_filename': validation_result.get('sanitized_filename', filename)
        }, status=status.HTTP_200_OK)
        
    except SecurityValidationError as e:
        # Log security validation failure
        log_validation(
            user_id=user.id,
            username=user.username,
            filename=filename,
            sanitized_filename=filename,
            content_type=content_type,
            validation_result={
                'is_valid': False,
                'errors': [str(e)],
                'warnings': [],
                'metadata': {},
                'sanitized_filename': filename
            }
        )
        
        logger.warning(
            f"Security validation failed for user {user.username}, "
            f"filename: {filename}, error: {str(e)}"
        )
        
        return Response({
            'status': 'error',
            'is_valid': False,
            'errors': [str(e)],
            'warnings': [],
            'metadata': {},
            'sanitized_filename': filename
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except ValidationError as e:
        # Log validation failure
        log_validation(
            user_id=user.id,
            username=user.username,
            filename=filename,
            sanitized_filename=filename,
            content_type=content_type,
            validation_result={
                'is_valid': False,
                'errors': [str(e)],
                'warnings': [],
                'metadata': {},
                'sanitized_filename': filename
            }
        )
        
        return Response({
            'status': 'error',
            'is_valid': False,
            'errors': [str(e)],
            'warnings': [],
            'metadata': {},
            'sanitized_filename': filename
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Unexpected error during content validation: {str(e)}")
        return Response({
            'status': 'error',
            'error': f'Validation error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_bulk_content(request):
    """
    POST /api/content-validation/bulk/
    Validate multiple content files before upload.
    
    Request (multipart/form-data):
    - files: Multiple files
    - content_types: JSON array of content types for each file (in same order)
    - filenames: Optional JSON array of filenames
    
    Response:
    {
        "total_count": int,
        "valid_count": int,
        "invalid_count": int,
        "results": [
            {
                "filename": str,
                "sanitized_filename": str,
                "is_valid": bool,
                "errors": List[str],
                "warnings": List[str],
                "metadata": Dict
            }
        ]
    }
    """
    if 'files' not in request.FILES:
        return Response(
            {'error': 'At least one file is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    files = request.FILES.getlist('files')
    content_types_str = request.data.get('content_types', '[]')
    filenames_str = request.data.get('filenames', '[]')
    
    # Parse JSON arrays
    import json
    try:
        content_types = json.loads(content_types_str)
        filenames = json.loads(filenames_str) if filenames_str else []
    except json.JSONDecodeError:
        return Response(
            {'error': 'Invalid JSON in content_types or filenames'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(content_types) != len(files):
        return Response(
            {'error': f'Number of content_types ({len(content_types)}) must match number of files ({len(files)})'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = request.user
    
    # Prepare file list for validation
    file_list = []
    for i, file_obj in enumerate(files):
        content_type = content_types[i]
        filename = filenames[i] if i < len(filenames) and filenames[i] else file_obj.name
        file_list.append((file_obj, content_type, filename))
    
    try:
        # Validate all files
        validation_results = BulkValidator.validate_files(file_list)
        
        # Log each validation
        for i, result_dict in enumerate(validation_results['results']):
            log_validation(
                user_id=user.id,
                username=user.username,
                filename=result_dict['filename'],
                sanitized_filename=result_dict.get('sanitized_filename', result_dict['filename']),
                content_type=content_types[i],
                validation_result={
                    'is_valid': result_dict['is_valid'],
                    'errors': result_dict.get('errors', []),
                    'warnings': result_dict.get('warnings', []),
                    'metadata': result_dict.get('metadata', {}),
                    'sanitized_filename': result_dict.get('sanitized_filename', result_dict['filename'])
                }
            )
        
        return Response({
            'status': 'success',
            **validation_results
        }, status=status.HTTP_200_OK)
        
    except ValidationError as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Unexpected error during bulk content validation: {str(e)}")
        return Response({
            'status': 'error',
            'error': f'Validation error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
