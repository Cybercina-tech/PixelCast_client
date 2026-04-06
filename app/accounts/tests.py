"""
Comprehensive tests for user management and security.

Tests cover authentication, authorization, password security, audit logging,
and account lockout functionality.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache
from django.core.exceptions import ValidationError
from unittest.mock import patch

from .models import User
from .security import AccountLockoutManager, PasswordStrengthChecker, sanitize_input
from .serializers import UserSerializer, LoginSerializer, ChangePasswordSerializer
from core.models import AuditLog
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class PasswordSecurityTests(TestCase):
    """Tests for password security and validation."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='Employee'
        )
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='plaintext123',
            role='Employee'
        )
        
        # Password should be hashed, not stored in plaintext
        self.assertNotEqual(user.password, 'plaintext123')
        self.assertTrue(user.has_usable_password())

        # But authentication should still work
        self.assertTrue(user.check_password('plaintext123'))
        self.assertFalse(user.check_password('wrongpassword'))
    
    def test_password_strength_checker(self):
        """Test password strength checking."""
        # Weak password
        result = PasswordStrengthChecker.check_password_strength('123')
        self.assertFalse(result['is_strong'])
        self.assertEqual(result['score'], 0)
        
        # Medium password (length >= 12 yields score 2 from length rules alone)
        result = PasswordStrengthChecker.check_password_strength('password1234')
        self.assertTrue(result['score'] >= 2)
        
        # Strong password
        result = PasswordStrengthChecker.check_password_strength('P@ssw0rd123!')
        self.assertTrue(result['is_strong'])
        self.assertTrue(result['score'] >= 3)
    
    def test_password_validation(self):
        """Test password validation in serializer."""
        serializer = ChangePasswordSerializer(
            data={
                'old_password': 'testpass123',
                'new_password': 'weak',
                'new_password_confirm': 'weak',
            },
            context={'request': type('obj', (object,), {'user': self.user})()}
        )
        
        # Should fail validation due to weak password
        self.assertFalse(serializer.is_valid())


class AccountLockoutTests(TestCase):
    """Tests for account lockout functionality."""
    
    def setUp(self):
        cache.clear()
        self.username = 'testuser'
    
    def test_failed_login_attempt_recording(self):
        """Test recording of failed login attempts."""
        is_locked, remaining = AccountLockoutManager.record_failed_attempt(self.username)
        
        self.assertFalse(is_locked)
        self.assertEqual(remaining, 4)  # 5 - 1
    
    def test_account_lockout_after_max_attempts(self):
        """Test account lockout after max attempts."""
        for i in range(5):
            is_locked, remaining = AccountLockoutManager.record_failed_attempt(self.username)
        
        self.assertTrue(is_locked)
        self.assertTrue(AccountLockoutManager.is_locked(self.username))
    
    def test_clear_failed_attempts(self):
        """Test clearing failed attempts after successful login."""
        AccountLockoutManager.record_failed_attempt(self.username)
        AccountLockoutManager.clear_failed_attempts(self.username)
        
        self.assertFalse(AccountLockoutManager.is_locked(self.username))
    
    def test_lockout_timeout(self):
        """Test that lockout expires after timeout."""
        # Record max attempts
        for i in range(5):
            AccountLockoutManager.record_failed_attempt(self.username)
        
        # Manually expire the lockout
        lockout_key = AccountLockoutManager.get_lockout_key(self.username)
        cache.delete(lockout_key)
        
        self.assertFalse(AccountLockoutManager.is_locked(self.username))


class AuthenticationTests(TestCase):
    """Tests for authentication endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='Employee',
            is_active=True
        )
        cache.clear()
    
    def test_successful_login(self):
        """Test successful login."""
        url = reverse('auth-login')
        response = self.client.post(url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
    
    def test_failed_login_account_lockout(self):
        """Test account lockout after multiple failed logins."""
        url = reverse('auth-login')
        
        # Make max attempts
        for i in range(5):
            response = self.client.post(url, {
                'username': 'testuser',
                'password': 'wrongpassword'
            })
        
        # Next attempt should be locked
        response = self.client.post(url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        # Django REST Framework uses 429 for rate limiting/lockout
        self.assertIn(response.status_code, [423, 429])  # Locked/Too Many Requests
        self.assertIn('lockout', response.data.get('error', '').lower())
    
    def test_prevent_user_enumeration(self):
        """Test that login doesn't reveal whether user exists."""
        url = reverse('auth-login')
        
        # Try with non-existent user
        response1 = self.client.post(url, {
            'username': 'nonexistent',
            'password': 'wrongpassword'
        })
        
        # Try with existing user, wrong password
        response2 = self.client.post(url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        # Both should return same error (prevent enumeration)
        self.assertEqual(response1.status_code, response2.status_code)
        self.assertNotIn('does not exist', str(response1.data).lower())
    
    def test_inactive_user_login(self):
        """Test that inactive users cannot login."""
        self.user.is_active = False
        self.user.save()
        
        url = reverse('auth-login')
        response = self.client.post(url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertIn(
            response.status_code,
            (status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED),
        )
    
    def test_logout(self):
        """Test logout functionality."""
        self.client.force_authenticate(user=self.user)
        url = reverse('auth-logout')
        
        # Omit invalid refresh token; blacklist is optional when absent
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserManagementTests(TestCase):
    """Tests for user CRUD operations."""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='Developer',
            is_active=True
        )
        self.viewer = User.objects.create_user(
            username='viewer',
            email='viewer@example.com',
            password='viewer123',
            role='Employee',
            is_active=True
        )
    
    def test_create_user_admin_only(self):
        """Test that only admins can create users."""
        self.client.force_authenticate(user=self.viewer)
        url = reverse('user-list')
        
        response = self.client.post(url, {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'role': 'Employee'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_user_success(self):
        """Test successful user creation by admin."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('user-list')
        
        response = self.client.post(url, {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongP@ss123',
            'password_confirm': 'StrongP@ss123',
            'role': 'Employee',
            'full_name': 'New User'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_change_password(self):
        """Test password change functionality."""
        self.client.force_authenticate(user=self.viewer)
        url = reverse('user-change-password', args=[self.viewer.id])
        
        response = self.client.post(url, {
            'old_password': 'viewer123',
            'new_password': 'NewP@ss123',
            'new_password_confirm': 'NewP@ss123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password changed
        self.viewer.refresh_from_db()
        self.assertTrue(self.viewer.check_password('NewP@ss123'))
    
    def test_change_role_admin_only(self):
        """Test that only admins can change roles."""
        self.client.force_authenticate(user=self.viewer)
        url = reverse('user-change-role', args=[self.viewer.id])
        
        response = self.client.post(url, {
            'role': 'Manager'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_developer_can_change_own_role(self):
        """Developers may change their own role via change_role (e.g. handoff)."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('user-change-role', args=[self.admin.id])
        response = self.client.post(url, {'role': 'Manager'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.role, 'Manager')
        self.assertFalse(self.admin.is_superuser)
    
    def test_delete_user(self):
        """Test user deletion."""
        user_to_delete = User.objects.create_user(
            username='todelete',
            email='delete@example.com',
            password='pass123',
            role='Employee'
        )
        
        self.client.force_authenticate(user=self.admin)
        url = reverse('user-detail', args=[user_to_delete.id])
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=user_to_delete.id).exists())
    
    def test_prevent_self_deletion(self):
        """Test that users cannot delete themselves."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('user-detail', args=[self.admin.id])
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AuditLoggingTests(TestCase):
    """Tests for audit logging in user management."""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='Developer'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123',
            role='Employee'
        )
    
    def test_login_audit_log(self):
        """Test that login is logged."""
        url = reverse('auth-login')
        response = self.client.post(url, {
            'username': 'admin',
            'password': 'admin123'
        })
        
        # Check audit log was created
        audit_logs = AuditLog.objects.filter(
            action_type='login',
            username='admin',
            success=True
        )
        self.assertTrue(audit_logs.exists())
    
    def test_user_creation_audit_log(self):
        """Test that user creation is logged."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('user-list')
        
        response = self.client.post(url, {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongP@ss123',
            'password_confirm': 'StrongP@ss123',
            'role': 'Employee'
        })
        
        # Check audit log
        audit_logs = AuditLog.objects.filter(
            action_type='create',
            resource_type='User',
            success=True
        )
        self.assertTrue(audit_logs.exists())
    
    def test_password_change_audit_log(self):
        """Test that password change is logged."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user-change-password', args=[self.user.id])
        
        response = self.client.post(url, {
            'old_password': 'test123',
            'new_password': 'NewP@ss123',
            'new_password_confirm': 'NewP@ss123'
        })
        
        # Check audit log
        audit_logs = AuditLog.objects.filter(
            action_type='password_change',
            user=self.user,
            success=True
        )
        self.assertTrue(audit_logs.exists())
        self.assertEqual(audit_logs.first().severity, 'high')
    
    def test_role_change_audit_log(self):
        """Test that role change is logged with critical severity."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('user-change-role', args=[self.user.id])
        
        response = self.client.post(url, {
            'role': 'Manager'
        })
        
        # Check audit log (cannot filter by GenericFK `resource=` without GenericRelation)
        user_ct = ContentType.objects.get_for_model(User)
        audit_logs = AuditLog.objects.filter(
            action_type='role_change',
            content_type=user_ct,
            object_id=str(self.user.pk),
            severity='critical',
        )
        self.assertTrue(audit_logs.exists())


class InputSanitizationTests(TestCase):
    """Tests for input sanitization."""
    
    def test_sanitize_input(self):
        """Test input sanitization."""
        # Null bytes
        result = sanitize_input('test\x00string')
        self.assertEqual(result, 'teststring')
        
        # Whitespace
        result = sanitize_input('  test  ')
        self.assertEqual(result, 'test')
        
        # Length limit
        long_string = 'a' * 2000
        result = sanitize_input(long_string)
        self.assertLessEqual(len(result), 1000)
    
    def test_email_normalization(self):
        """Test email normalization in serializer."""
        serializer = UserSerializer()
        normalized = serializer.validate_email('Test@Example.COM')
        
        self.assertEqual(normalized, 'test@example.com')


class PermissionTests(TestCase):
    """Tests for role-based permissions."""
    
    def setUp(self):
        self.superadmin = User.objects.create_user(
            username='superadmin',
            email='superadmin@example.com',
            password='pass123',
            role='Developer'
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass123',
            role='Developer'
        )
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='pass123',
            role='Manager'
        )
        self.viewer = User.objects.create_user(
            username='viewer',
            email='viewer@example.com',
            password='pass123',
            role='Employee'
        )
        self.visitor = User.objects.create_user(
            username='visitor',
            email='visitor@example.com',
            password='pass123',
            role='Visitor'
        )
    
    def test_permission_methods(self):
        """Test permission helper methods."""
        self.assertTrue(self.superadmin.has_full_access())
        self.assertTrue(self.admin.has_full_access())
        self.assertFalse(self.manager.has_full_access())
        
        self.assertTrue(self.manager.can_manage_own_resources())
        self.assertTrue(self.viewer.can_manage_own_resources())
        self.assertFalse(self.visitor.can_manage_own_resources())
        self.assertTrue(self.visitor.has_read_only_access())

    def test_role_checks(self):
        """Test role checking methods."""
        self.assertTrue(self.superadmin.is_developer())
        self.assertTrue(self.admin.is_developer())
        self.assertTrue(self.manager.is_manager())
        self.assertTrue(self.viewer.is_employee())
        self.assertTrue(self.visitor.is_visitor())


class SecurityEdgeCasesTests(TestCase):
    """Tests for security edge cases."""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='Developer'
        )
    
    def test_xss_prevention(self):
        """Test XSS prevention in user input."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('user-list')
        
        # Try to inject script
        response = self.client.post(url, {
            'username': '<script>alert("xss")</script>',
            'email': '<script>alert("xss")</script>@example.com',
            'password': 'StrongP@ss123',
            'password_confirm': 'StrongP@ss123',
            'role': 'Employee'
        })
        
        # Should sanitize or reject
        if response.status_code == status.HTTP_201_CREATED:
            user = User.objects.get(username='<script>alert("xss")</script>')
            # Script tags should be removed or escaped
            self.assertNotIn('<script>', user.username)
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('user-list')
        
        # Try SQL injection in username
        response = self.client.post(url, {
            'username': "admin'; DROP TABLE users; --",
            'email': 'test@example.com',
            'password': 'StrongP@ss123',
            'password_confirm': 'StrongP@ss123',
            'role': 'Employee'
        })
        
        # Should handle safely (either reject or sanitize)
        # Most importantly, users table should still exist
        self.assertTrue(User.objects.filter(role='Developer').exists())


# Integration tests
class UserManagementIntegrationTests(TestCase):
    """Integration tests for complete user management workflows."""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='Developer'
        )
        cache.clear()
    
    def test_complete_user_lifecycle(self):
        """Test complete user lifecycle: create, update, delete."""
        self.client.force_authenticate(user=self.admin)
        
        # Create user
        create_url = reverse('user-list')
        create_response = self.client.post(create_url, {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongP@ss123',
            'password_confirm': 'StrongP@ss123',
            'role': 'Employee'
        })
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        user_id = create_response.data['id']
        
        # Update user
        update_url = reverse('user-detail', args=[user_id])
        update_response = self.client.patch(update_url, {
            'full_name': 'New User Name'
        })
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        
        # Delete user
        delete_response = self.client.delete(update_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify audit logs created
        self.assertTrue(AuditLog.objects.filter(action_type='create').exists())
        self.assertTrue(AuditLog.objects.filter(action_type='update').exists())
        self.assertTrue(AuditLog.objects.filter(action_type='delete', severity='critical').exists())
