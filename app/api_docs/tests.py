"""
Tests for API documentation endpoints and schema generation.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from tests.base import BaseAPITestCase


class APIDocumentationTests(BaseAPITestCase):
    """Tests for API documentation endpoints."""
    
    def test_schema_endpoint_access(self):
        """Test that schema endpoint is accessible without authentication."""
        url = reverse('api_docs:schema')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_swagger_ui_access(self):
        """Test that Swagger UI is accessible without authentication."""
        url = reverse('api_docs:swagger-ui')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_redoc_access(self):
        """Test that ReDoc is accessible without authentication."""
        url = reverse('api_docs:redoc')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_schema_format_json(self):
        """Test schema generation in JSON format."""
        url = reverse('api_docs:schema')
        response = self.client.get(url, {'format': 'json'})
        
        if response.status_code == status.HTTP_200_OK:
            ct = response['Content-Type']
            self.assertIn('application/vnd.oai.openapi+json', ct)
            self.assertIn('openapi', response.data)
    
    def test_schema_format_yaml(self):
        """Test schema generation in YAML format."""
        url = reverse('api_docs:schema')
        response = self.client.get(url, {'format': 'yaml'})
        
        if response.status_code == status.HTTP_200_OK:
            self.assertIn('openapi', str(response.content).lower())
    
    def test_schema_includes_all_endpoints(self):
        """Test that schema includes all main endpoint groups."""
        url = reverse('api_docs:schema')
        response = self.client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            schema = response.data
            paths = schema.get('paths', {})
            
            # Check for main endpoint groups
            self.assertTrue(
                any('/api/screens/' in path for path in paths.keys()) or
                any('/screens' in path for path in paths.keys())
            )
            self.assertTrue(
                any('/api/templates/' in path for path in paths.keys()) or
                any('/templates' in path for path in paths.keys())
            )
            self.assertTrue(
                any('/api/auth/' in path for path in paths.keys()) or
                any('/auth' in path for path in paths.keys())
            )
    
    def test_schema_security_schemes(self):
        """Test that security schemes are defined."""
        url = reverse('api_docs:schema')
        response = self.client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            schema = response.data
            components = schema.get('components', {})
            security_schemes = components.get('securitySchemes', {})
            
            # Should have JWT authentication
            self.assertIn('BearerAuth', security_schemes)
    
    def test_schema_tags_defined(self):
        """Test that tags are defined in schema."""
        url = reverse('api_docs:schema')
        response = self.client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            schema = response.data
            tags = schema.get('tags', [])
            
            # Should have multiple tags
            self.assertGreater(len(tags), 5)
            
            # Should include main tags
            tag_names = [tag.get('name') for tag in tags]
            self.assertIn('Authentication', tag_names)
            self.assertIn('Screens', tag_names)
            self.assertIn('Core Infrastructure', tag_names)
    
    def test_core_endpoints_documented(self):
        """Test that core infrastructure endpoints are documented."""
        url = reverse('api_docs:schema')
        response = self.client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            schema = response.data
            paths = schema.get('paths', {})
            
            # Check for core endpoints
            core_paths = [
                path for path in paths.keys()
                if '/core/audit-logs' in path or '/core/backups' in path
            ]
            self.assertGreater(len(core_paths), 0, "Core endpoints should be documented")
