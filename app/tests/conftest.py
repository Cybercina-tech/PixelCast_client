"""
Pytest configuration and shared fixtures.
"""
import pytest


def pytest_collection_modifyitems(config, items):
    """Run APIPermissionTests last to avoid DRF client/session pollution from other tests."""
    tail = [i for i in items if 'APIPermissionTests' in i.nodeid]
    if not tail:
        return
    head = [i for i in items if 'APIPermissionTests' not in i.nodeid]
    items[:] = head + tail
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


@pytest.fixture
def api_client():
    """Create API client for testing."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Create authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def superadmin_user(db):
    """Create a Developer (full access) user."""
    return User.objects.create_user(
        username='superadmin',
        email='superadmin@test.com',
        password='testpass123',
        role='Developer',
        is_active=True,
        is_superuser=True,
        is_staff=True,
    )


@pytest.fixture
def admin_user(db):
    """Alias: second Developer-style account for tests expecting 'admin' name."""
    return User.objects.create_user(
        username='admin',
        email='admin@test.com',
        password='testpass123',
        role='Developer',
        is_active=True,
        is_superuser=True,
        is_staff=True,
    )


@pytest.fixture
def manager_user(db):
    """Create a manager user."""
    return User.objects.create_user(
        username='manager',
        email='manager@test.com',
        password='testpass123',
        role='Manager',
        organization_name='TestOrg',
        is_active=True
    )


@pytest.fixture
def operator_user(db):
    """Create an employee user (legacy fixture name)."""
    return User.objects.create_user(
        username='operator',
        email='operator@test.com',
        password='testpass123',
        role='Employee',
        organization_name='TestOrg',
        is_active=True
    )


@pytest.fixture
def viewer_user(db):
    """Create an employee user (legacy fixture name)."""
    return User.objects.create_user(
        username='viewer',
        email='viewer@test.com',
        password='testpass123',
        role='Employee',
        organization_name='TestOrg',
        is_active=True
    )


@pytest.fixture
def user(db):
    """Create a default user (manager role)."""
    return User.objects.create_user(
        username='testuser',
        email='test@test.com',
        password='testpass123',
        role='Manager',
        organization_name='TestOrg',
        is_active=True
    )


@pytest.fixture
def screen(db, user):
    """Create a test screen."""
    from signage.models import Screen
    return Screen.objects.create(
        name='Test Screen',
        device_id='test-device-001',
        location='Test Location',
        owner=user,
        is_online=True
    )


@pytest.fixture
def template(db, user):
    """Create a test template."""
    from templates.models import Template
    return Template.objects.create(
        name='Test Template',
        description='Test Description',
        width=1920,
        height=1080,
        created_by=user,
        is_active=True
    )


@pytest.fixture
def content(db, template, user):
    """Create a test content."""
    from templates.models import Layer, Widget, Content
    layer = Layer.objects.create(
        name='Test Layer',
        template=template,
        width=1920,
        height=1080
    )
    widget = Widget.objects.create(
        name='Test Widget',
        type='text',
        layer=layer
    )
    return Content.objects.create(
        name='Test Content',
        type='text',
        widget=widget
    )


@pytest.fixture
def schedule(db, template, screen):
    """Create a test schedule."""
    from templates.models import Schedule
    schedule = Schedule.objects.create(
        name='Test Schedule',
        template=template,
        start_time=timezone.now(),
        end_time=timezone.now() + timedelta(hours=1),
        is_active=True
    )
    schedule.screens.add(screen)
    return schedule


@pytest.fixture
def command(db, screen, user):
    """Create a test command."""
    from commands.models import Command
    return Command.objects.create(
        name='Test Command',
        type='refresh',
        screen=screen,
        created_by=user,
        status='pending'
    )
