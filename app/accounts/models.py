import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission, UserManager as DjangoUserManager
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import logging
import random
from .validators import validate_username_format, validate_phone_number, validate_organization_name

logger = logging.getLogger(__name__)


# Validators
phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)

email_validator = EmailValidator()


class UserManager(DjangoUserManager):
    """Ensures Django superusers always get Developer role (matches RBAC hierarchy)."""

    use_in_migrations = True

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields['is_staff'] = True
        extra_fields['is_superuser'] = True
        extra_fields['role'] = 'Developer'
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model for Digital Signage System.
    
    Extends Django's AbstractUser to add role-based access control,
    organization support, and additional user information.
    """
    
    # Core Information
    email = models.EmailField(
        unique=True,
        validators=[email_validator],
        help_text="User email address (required and unique)",
        db_index=True,
    )
    full_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="User's full name",
        db_index=True,
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[validate_phone_number],
        help_text="User's phone number"
    )
    
    # Role & Permissions (Developer > Manager > Employee > Visitor)
    ROLE_CHOICES = [
        ('Developer', 'Developer'),
        ('Manager', 'Manager'),
        ('Employee', 'Employee'),
        ('Visitor', 'Visitor'),
    ]
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='Employee',
        help_text="User role in the system"
    )
    
    # Multi-Tenant & Organization
    organization_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        validators=[validate_organization_name],
        help_text="Organization name for multi-tenant support"
    )
    tenant = models.ForeignKey(
        'saas_platform.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="SaaS customer account (Platform); optional for legacy installs",
    )

    # Security fields
    failed_login_attempts = models.IntegerField(
        default=0,
        help_text="Number of consecutive failed login attempts"
    )
    locked_until = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Account lockout expiration time"
    )
    
    # Email verification fields
    is_email_verified = models.BooleanField(
        default=False,
        help_text="Whether the user's email address has been verified"
    )
    verification_code = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        help_text="6-digit verification code for email verification"
    )
    verification_code_expiry = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Expiration time for the verification code"
    )

    # Two-factor authentication (TOTP)
    totp_secret = models.CharField(
        max_length=64,
        blank=True,
        default='',
        help_text="Base32 TOTP secret (empty when 2FA not configured)",
    )
    is_2fa_enabled = models.BooleanField(
        default=False,
        help_text="When True, login requires a TOTP code after password",
    )
    backup_codes_hash = models.TextField(
        blank=True,
        default='',
        help_text="JSON list of hashed one-time backup codes (empty when none)",
    )

    # SSO extension (OIDC/SAML) — populated when using enterprise SSO
    sso_provider = models.CharField(
        max_length=64,
        blank=True,
        default='',
        db_index=True,
        help_text="e.g. google, azure, oidc",
    )
    sso_subject = models.CharField(
        max_length=255,
        blank=True,
        default='',
        db_index=True,
        help_text="Stable subject identifier from the IdP",
    )
    
    # Admin lock (Developer can hard-lock any user)
    is_admin_locked = models.BooleanField(
        default=False,
        help_text="Developer-imposed hard lock — blocks login and revokes sessions",
    )
    admin_lock_reason = models.CharField(
        max_length=255, blank=True, default='',
        help_text="Reason shown in admin tools when account is locked",
    )
    admin_lock_until = models.DateTimeField(
        null=True, blank=True,
        help_text="Optional expiration; null means locked until manually unlocked",
    )

    # Status & Metadata
    last_seen = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last time user was seen (login or heartbeat)"
    )
    date_joined = models.DateTimeField(
        default=timezone.now,
        help_text="Date and time when user account was created"
    )

    onboarding_progress = models.JSONField(
        default=dict,
        blank=True,
        help_text="Product onboarding checklist progress (tenant-scoped keys)",
    )

    objects = UserManager()
    
    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined', 'username']
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['organization_name', 'role']),
        ]
    
    def __str__(self):
        """Return full_name if available, otherwise username"""
        return self.full_name if self.full_name else self.username
    
    # Role Helper Methods
    def is_developer(self):
        """Top tier: full system access (god mode)."""
        return self.role == 'Developer' or self.is_superuser

    def is_superadmin(self):
        """Alias for is_developer() — backward compatible name."""
        return self.is_developer()

    def is_manager(self):
        """Staff tier: manage employees, content, screens; not system settings."""
        return self.role == 'Manager'

    def is_employee(self):
        """Operational tier: screens, schedules, media only."""
        if self.is_superuser:
            return False
        return self.role == 'Employee'

    def is_visitor(self):
        """Read-mostly tier: dashboard and template preview/edit without persist."""
        if self.is_superuser:
            return False
        return self.role == 'Visitor'

    def is_admin(self):
        """Deprecated: old Admin role; use is_developer()."""
        return False

    def is_operator(self):
        """Deprecated: old Operator role."""
        return False

    def is_viewer(self):
        """Deprecated: old Viewer role."""
        return False

    # Permission Helper Methods
    def has_full_access(self):
        """Full access (Developer only)."""
        return self.is_developer()

    def can_manage_own_resources(self):
        """Developer, Manager, and Employee may manage permitted resources; Visitor may not."""
        return self.is_developer() or self.is_manager() or self.is_employee()

    def has_read_only_access(self):
        """Visitor tier: UI read / local edit without server-side saves."""
        return self.is_visitor()

    def can_execute_commands(self):
        """Developer, Manager, and Employee may create and execute commands (screen access still enforced per request)."""
        return self.is_developer() or self.is_manager() or self.is_employee()

    def can_manage_templates(self):
        """Legacy helper: Developer/Manager full template management. Employees use create_templates/edit_templates + own-resource checks."""
        return self.is_developer() or self.is_manager()

    def can_view_reports(self):
        """Analytics/reports: Developer and Manager (not system logs for Manager — use sidebar/API)."""
        return self.is_developer() or self.is_manager()

    def can_manage_employees(self):
        """Managers may manage Employee users only; Developers manage all."""
        return self.is_developer() or self.is_manager()
    
    # Property Methods for Resource Counts
    @property
    def active_screens_count(self):
        """Count of active Screens owned by this user"""
        try:
            from signage.models import Screen
            return Screen.objects.filter(owner=self, is_online=True).count()
        except ImportError:
            return 0
    
    @property
    def total_screens_count(self):
        """Total count of Screens owned by this user"""
        try:
            from signage.models import Screen
            return Screen.objects.filter(owner=self).count()
        except ImportError:
            return 0
    
    @property
    def active_templates_count(self):
        """Count of active Templates created by this user"""
        try:
            from templates.models import Template
            return Template.objects.filter(created_by=self, is_active=True).count()
        except ImportError:
            return 0
    
    @property
    def total_templates_count(self):
        """Total count of Templates created by this user"""
        try:
            from templates.models import Template
            return Template.objects.filter(created_by=self).count()
        except ImportError:
            return 0
    
    @property
    def storage_used_bytes(self):
        """Total file storage consumed by content in templates owned by this user."""
        try:
            from django.db.models import Sum
            from templates.models import Content
            result = Content.objects.filter(
                widget__layer__template__created_by=self,
                file_size__isnull=False,
            ).aggregate(total=Sum('file_size'))
            return result['total'] or 0
        except Exception:
            return 0

    @property
    def subscription_plan(self):
        """Plan name from the user's tenant, or None."""
        tenant = getattr(self, 'tenant', None)
        if tenant:
            return getattr(tenant, 'plan_name', '') or None
        return None

    @property
    def subscription_status(self):
        """Subscription status from the user's tenant, or None."""
        tenant = getattr(self, 'tenant', None)
        if tenant:
            return getattr(tenant, 'subscription_status', '') or None
        return None

    # Organization Helper Methods
    def get_organization_users(self):
        """Get all users in the same organization"""
        if not self.organization_name:
            return User.objects.none()
        return User.objects.filter(
            organization_name=self.organization_name,
            is_active=True
        )

    def get_accessible_templates_queryset(self):
        """Templates this user may read in the API (includes sample templates for Visitors)."""
        from django.db.models import Q
        from templates.models import Template

        qs = Template.objects.all()
        if self.has_full_access():
            return qs
        if self.is_visitor():
            q = Q(is_sample=True)
            if self.organization_name:
                org_users = self.get_organization_users()
                q |= Q(created_by=self) | Q(created_by__in=org_users)
            return qs.filter(q)
        if self.can_manage_own_resources():
            org_users = self.get_organization_users()
            return qs.filter(Q(created_by=self) | Q(created_by__in=org_users))
        return qs.filter(created_by=self)
    
    def can_access_user_resource(self, other_user):
        """
        Check if this user can access resources of another user.
        Developer can access all; others may access same organization or own resources.
        """
        if self.is_developer():
            return True
        if self.id == other_user.id:
            return True
        if self.organization_name and other_user.organization_name:
            return self.organization_name == other_user.organization_name
        return False
    
    # Update last_seen method
    def update_last_seen(self):
        """Update last_seen timestamp to current time"""
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])
    
    def generate_verification_code(self):
        """Generate a 6-digit random verification code and set expiry to 10 minutes from now"""
        code = str(random.randint(100000, 999999))  # Generate 6-digit code
        self.verification_code = code
        self.verification_code_expiry = timezone.now() + timedelta(minutes=10)
        self.save(update_fields=['verification_code', 'verification_code_expiry'])
        return code
    
    def clean(self):
        """Validate model fields"""
        from django.core.exceptions import ValidationError
        
        # Validate username format
        if self.username:
            try:
                validate_username_format(self.username)
            except ValidationError as e:
                raise ValidationError({'username': e.messages})
        
        # Validate email
        if self.email:
            self.email = self.email.lower()
        
        # Validate organization name
        if self.organization_name:
            try:
                validate_organization_name(self.organization_name)
            except ValidationError as e:
                raise ValidationError({'organization_name': e.messages})
        
        super().clean()
    
    # Override save to ensure email is unique and lowercase
    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        if self.is_superuser and (self.role != 'Developer' or not self.is_staff):
            self.role = 'Developer'
            self.is_staff = True
            if update_fields is not None:
                kwargs['update_fields'] = list(set(update_fields) | {'role', 'is_staff'})

        # Run clean validation
        self.full_clean()
        
        if self.email:
            self.email = self.email.lower()
        if not self.username:
            self.username = self.email
        
        # Validate username format on save
        if self.username:
            try:
                validate_username_format(self.username)
            except ValidationError:
                # If username validation fails, log but don't crash (for backward compatibility)
                logger.warning(f'Username validation warning for user {self.username}')
        
        super().save(*args, **kwargs)


class UserInvitation(models.Model):
    """Pending invitation to join a tenant with a given role."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(db_index=True)
    token = models.CharField(max_length=128, unique=True, db_index=True)
    role = models.CharField(max_length=20, default='Employee')
    tenant = models.ForeignKey(
        'saas_platform.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='invitations',
    )
    invited_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='sent_invitations',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'accounts_user_invitation'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        from .invitations import create_invitation_token, default_invite_expiry

        if not self.expires_at:
            self.expires_at = default_invite_expiry()
        if not self.token:
            self.token = create_invitation_token()
        super().save(*args, **kwargs)

    def is_valid(self) -> bool:
        return self.accepted_at is None and self.expires_at > timezone.now()


# Signals are handled in accounts/signals.py
