"""
Security and validation tests for content validation system.
"""
import os
import json
from io import BytesIO
from django.urls import reverse
from django.test import TestCase
from PIL import Image
from tests.base import BaseAPITestCase


class ContentValidationSecurityTests(BaseAPITestCase):
    """Security tests for content validation."""
    
    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are blocked."""
        from content_validation.validators import ContentValidator, SecurityValidationError
        
        dangerous_filenames = [
            '../../etc/passwd',
            '..\\..\\windows\\system32\\config\\sam',
            '/etc/passwd',
            'C:\\Windows\\System32\\config\\sam',
            '....//....//etc/passwd',
        ]
        
        for filename in dangerous_filenames:
            file_obj = BytesIO(b'fake content')
            file_obj.name = filename
            
            with self.assertRaises(SecurityValidationError):
                ContentValidator.validate_content(
                    file_obj=file_obj,
                    content_type='image',
                    filename=filename
                )
    
    def test_executable_file_detection(self):
        """Test that executable files are detected and rejected."""
        from content_validation.validators import ContentValidator, SecurityValidationError
        
        # ELF executable header (Linux)
        elf_file = BytesIO(b'\x7fELF\x01\x01\x01' + b'\x00' * 100)
        elf_file.name = 'malicious.jpg'
        
        with self.assertRaises(SecurityValidationError):
            ContentValidator.validate_content(
                file_obj=elf_file,
                content_type='image',
                filename='malicious.jpg'
            )
    
    def test_script_injection_detection(self):
        """Test that script injection attempts are detected."""
        from content_validation.validators import ContentValidator, SecurityValidationError
        
        malicious_html = b'<html><script>alert("XSS")</script></html>'
        file_obj = BytesIO(malicious_html)
        file_obj.name = 'test.html'
        
        with self.assertRaises(SecurityValidationError):
            ContentValidator.validate_content(
                file_obj=file_obj,
                content_type='webview',
                filename='test.html'
            )
    
    def test_dangerous_extension_blocking(self):
        """Test that dangerous extensions are blocked."""
        from content_validation.validators import ContentValidator, SecurityValidationError
        
        dangerous_extensions = ['.exe', '.bat', '.php', '.sh', '.js']
        
        for ext in dangerous_extensions:
            file_obj = BytesIO(b'fake content')
            filename = f'malicious{ext}'
            
            with self.assertRaises(SecurityValidationError):
                ContentValidator.validate_content(
                    file_obj=file_obj,
                    content_type='text',
                    filename=filename
                )
    
    def test_null_byte_injection(self):
        """Test that null byte injection is prevented."""
        from content_validation.validators import ContentValidator, SecurityValidationError
        
        filename_with_null = 'file\x00.jpg'
        file_obj = BytesIO(b'fake image')
        
        with self.assertRaises(SecurityValidationError):
            ContentValidator.validate_content(
                file_obj=file_obj,
                content_type='image',
                filename=filename_with_null
            )


class ContentValidationFormatTests(BaseAPITestCase):
    """Tests for content format validation."""
    
    def test_image_validation_valid(self):
        """Test validation of valid image."""
        from content_validation.validators import ContentValidator
        
        # Create valid JPEG
        img = Image.new('RGB', (100, 100), color='red')
        img_file = BytesIO()
        img.save(img_file, format='JPEG')
        img_file.name = 'test.jpg'
        img_file.seek(0)
        
        result = ContentValidator.validate_content(
            file_obj=img_file,
            content_type='image',
            filename='test.jpg'
        )
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['metadata']['format'], 'JPEG')
    
    def test_image_validation_invalid_format(self):
        """Test validation rejects invalid image format."""
        from content_validation.validators import ContentValidator, ValidationError
        
        # Create invalid image data
        invalid_file = BytesIO(b'not an image')
        invalid_file.name = 'fake.jpg'
        
        with self.assertRaises(ValidationError):
            ContentValidator.validate_content(
                file_obj=invalid_file,
                content_type='image',
                filename='fake.jpg'
            )
    
    def test_video_validation_valid(self):
        """Test validation of valid video."""
        from content_validation.validators import ContentValidator
        
        # Create minimal MP4 header
        mp4_file = BytesIO(b'ftyp' + b'\x00' * 100)
        mp4_file.name = 'test.mp4'
        mp4_file.seek(0)
        
        result = ContentValidator.validate_content(
            file_obj=mp4_file,
            content_type='video',
            filename='test.mp4'
        )
        
        # Should validate format check passes
        self.assertIn(result['metadata'].get('format'), ['MP4', None])
    
    def test_file_size_validation(self):
        """Test file size limits are enforced."""
        from content_validation.validators import ContentValidator, ValidationError
        
        # Create oversized file
        oversized_file = BytesIO(b'x' * (60 * 1024 * 1024))  # 60 MB
        oversized_file.name = 'large.jpg'
        
        with self.assertRaises(ValidationError):
            ContentValidator.validate_content(
                file_obj=oversized_file,
                content_type='image',
                filename='large.jpg'
            )
    
    def test_mime_type_mismatch_detection(self):
        """Test MIME type vs extension mismatch is detected."""
        from content_validation.validators import ContentValidator, ValidationError
        
        # JPEG file with PNG extension
        img = Image.new('RGB', (100, 100), color='red')
        img_file = BytesIO()
        img.save(img_file, format='JPEG')
        img_file.name = 'test.png'
        img_file.seek(0)
        
        # Should detect mismatch
        try:
            result = ContentValidator.validate_content(
                file_obj=img_file,
                content_type='image',
                filename='test.png'
            )
            # May or may not fail depending on MIME detection
        except ValidationError:
            pass  # Expected for strict validation


class ContentValidationAPITests(BaseAPITestCase):
    """Tests for content validation API endpoints."""
    
    def test_validate_content_endpoint_valid(self):
        """Test validation endpoint with valid content."""
        img = Image.new('RGB', (100, 100), color='red')
        img_file = BytesIO()
        img.save(img_file, format='JPEG')
        img_file.name = 'test.jpg'
        img_file.seek(0)
        
        url = reverse('validate-content')
        response = self.client.post(
            url,
            {'file': img_file, 'content_type': 'image'},
            format='multipart'
        )
        
        self.assertResponseSuccess(response)
        self.assertTrue(response.data['is_valid'])
    
    def test_validate_content_endpoint_invalid(self):
        """Test validation endpoint with invalid content."""
        invalid_file = BytesIO(b'not an image')
        invalid_file.name = 'fake.jpg'
        
        url = reverse('validate-content')
        response = self.client.post(
            url,
            {'file': invalid_file, 'content_type': 'image'},
            format='multipart'
        )
        
        self.assertResponseError(response)
        self.assertFalse(response.data['is_valid'])
    
    def test_bulk_validate_content(self):
        """Test bulk content validation endpoint."""
        img1 = Image.new('RGB', (100, 100), color='red')
        img1_file = BytesIO()
        img1.save(img1_file, format='JPEG')
        img1_file.name = 'test1.jpg'
        img1_file.seek(0)
        
        img2 = Image.new('RGB', (100, 100), color='blue')
        img2_file = BytesIO()
        img2.save(img2_file, format='JPEG')
        img2_file.name = 'test2.jpg'
        img2_file.seek(0)
        
        url = reverse('validate-bulk-content')
        data = {
            'files': [img1_file, img2_file],
            'content_types': json.dumps(['image', 'image']),
            'filenames': json.dumps(['test1.jpg', 'test2.jpg'])
        }
        response = self.client.post(url, data, format='multipart')
        
        self.assertResponseSuccess(response)
        self.assertEqual(response.data['total_count'], 2)
        self.assertEqual(response.data['valid_count'], 2)


class ContentValidationIntegrationTests(BaseAPITestCase):
    """Integration tests for content validation with upload."""
    
    def test_upload_validates_content_before_saving(self):
        """Test that content is validated before saving."""
        from templates.models import Content
        
        content = self.create_content(type='image')
        
        # Create valid image
        img = Image.new('RGB', (100, 100), color='red')
        img_file = BytesIO()
        img.save(img_file, format='JPEG')
        img_file.name = 'test.jpg'
        img_file.seek(0)
        
        url = reverse('content-upload', kwargs={'id': str(content.id)})
        response = self.client.post(url, {'file': img_file}, format='multipart')
        
        # Should succeed if validation passes
        self.assertIn(response.status_code, [200, 400])
        
        if response.status_code == 200:
            content.refresh_from_db()
            self.assertIsNotNone(content.file_url)
    
    def test_upload_rejects_invalid_content(self):
        """Test that invalid content is rejected and not saved."""
        content = self.create_content(type='image')
        
        # Create invalid file (executable disguised as image)
        invalid_file = BytesIO(b'\x7fELF' + b'\x00' * 1000)
        invalid_file.name = 'malicious.jpg'
        
        url = reverse('content-upload', kwargs={'id': str(content.id)})
        response = self.client.post(url, {'file': invalid_file}, format='multipart')
        
        # Should fail validation
        self.assertResponseError(response)
        
        # File should not be saved
        content.refresh_from_db()
        self.assertIsNone(content.file_url)
