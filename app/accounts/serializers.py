from rest_framework import serializers
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError

from core.deployment import is_client_deployment
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings as jwt_api_settings
import logging
from .models import User
from .tokens import ScreenGramRefreshToken

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    active_screens_count = serializers.IntegerField(read_only=True)
    total_screens_count = serializers.IntegerField(read_only=True)
    active_templates_count = serializers.IntegerField(read_only=True)
    total_templates_count = serializers.IntegerField(read_only=True)
    storage_used_bytes = serializers.IntegerField(read_only=True)
    subscription_plan = serializers.CharField(read_only=True)
    subscription_status = serializers.CharField(read_only=True)
    tenant_id = serializers.SerializerMethodField()
    tenant_name = serializers.SerializerMethodField()
    is_lock_active = serializers.SerializerMethodField()
    admin_lock_reason = serializers.CharField(read_only=True)
    tenant_restriction = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'phone_number',
            'role', 'role_display', 'organization_name', 'tenant_id', 'tenant_name', 'is_active',
            'is_staff', 'is_superuser', 'is_email_verified', 'is_2fa_enabled', 'onboarding_progress',
            'last_seen', 'date_joined',
            'active_screens_count', 'total_screens_count',
            'active_templates_count', 'total_templates_count',
            'storage_used_bytes', 'subscription_plan', 'subscription_status',
            'is_lock_active', 'admin_lock_reason', 'tenant_restriction',
            'password'
        ]
        read_only_fields = [
            'id', 'is_staff', 'is_superuser', 'is_email_verified', 'is_2fa_enabled', 'last_seen', 'date_joined', 'tenant_id',
            'is_lock_active', 'admin_lock_reason', 'tenant_restriction',
            'storage_used_bytes', 'subscription_plan', 'subscription_status', 'tenant_name',
        ]
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
        }
    
    def validate_email(self, value):
        """Validate email is unique and properly formatted"""
        if not value:
            raise serializers.ValidationError("Email is required.")
        
        # Sanitize and normalize
        value = value.strip().lower()
        
        # Validate format
        from django.core.validators import validate_email as django_validate_email
        try:
            django_validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Enter a valid email address.")
        
        # Check uniqueness
        if self.instance and self.instance.email == value:
            return value
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        return value
    
    def validate_username(self, value):
        """Validate username is unique and follows rules"""
        if not value:
            raise serializers.ValidationError("Username is required.")
        
        # Sanitize
        value = value.strip()
        
        # Validate length
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters.")
        if len(value) > 150:
            raise serializers.ValidationError("Username is too long.")
        
        # Check uniqueness
        if self.instance and self.instance.username == value:
            return value
        
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        
        return value

    def get_tenant_id(self, obj):
        tid = getattr(obj, 'tenant_id', None)
        if tid is None:
            return None
        return str(tid)

    def get_tenant_name(self, obj):
        tenant = getattr(obj, 'tenant', None)
        return tenant.name if tenant else None

    def get_is_lock_active(self, obj):
        if not getattr(obj, 'is_admin_locked', False):
            return False
        lock_until = getattr(obj, 'admin_lock_until', None)
        if lock_until:
            from django.utils import timezone
            if lock_until <= timezone.now():
                return False
        return True

    def get_tenant_restriction(self, obj):
        tenant = getattr(obj, 'tenant', None)
        if tenant and getattr(tenant, 'access_locked', False):
            if tenant.is_access_lock_active():
                return {
                    'kind': 'tenant_access_lock',
                    'reason': tenant.access_lock_reason or '',
                }
        return None

    def create(self, validated_data):
        """Create user with hashed password"""
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user, handling password separately"""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserListSerializer(serializers.ModelSerializer):
    """List serializer with per-user metrics for the Super Admin global users console."""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    tenant_id = serializers.SerializerMethodField()
    tenant_name = serializers.SerializerMethodField()
    is_lock_active = serializers.SerializerMethodField()
    admin_lock_reason = serializers.CharField(read_only=True)
    total_screens_count = serializers.IntegerField(read_only=True)
    active_screens_count = serializers.IntegerField(read_only=True)
    total_templates_count = serializers.IntegerField(read_only=True)
    storage_used_bytes = serializers.IntegerField(read_only=True)
    subscription_plan = serializers.CharField(read_only=True)
    subscription_status = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'role',
            'role_display', 'organization_name', 'is_active',
            'last_seen', 'date_joined',
            'tenant_id', 'tenant_name',
            'is_lock_active', 'admin_lock_reason',
            'total_screens_count', 'active_screens_count',
            'total_templates_count', 'storage_used_bytes',
            'subscription_plan', 'subscription_status',
        ]
        read_only_fields = ['id', 'last_seen', 'date_joined']

    def get_tenant_id(self, obj):
        tid = getattr(obj, 'tenant_id', None)
        return str(tid) if tid else None

    def get_tenant_name(self, obj):
        tenant = getattr(obj, 'tenant', None)
        return tenant.name if tenant else None

    def get_is_lock_active(self, obj):
        if not getattr(obj, 'is_admin_locked', False):
            return False
        lock_until = getattr(obj, 'admin_lock_until', None)
        if lock_until:
            from django.utils import timezone
            if lock_until <= timezone.now():
                return False
        return True


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users"""
    id = serializers.IntegerField(read_only=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        allow_blank=False,
        trim_whitespace=False,
        validators=[validate_password],
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        allow_blank=False,
        trim_whitespace=False,
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'password_confirm',
            'full_name', 'phone_number', 'role', 'organization_name'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'role': {'default': 'Employee'},
        }
    
    def validate(self, attrs):
        """Validate password confirmation and strength"""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        if password != password_confirm:
            raise serializers.ValidationError({"password_confirm": "Password fields didn't match."})

        # Check password strength
        from .security import PasswordStrengthChecker
        strength = PasswordStrengthChecker.check_password_strength(password)

        if strength['score'] < 2 and strength['feedback']:
            logger.warning(f'Weak password detected during user create: {strength["feedback"]}')

        if is_client_deployment(getattr(settings, 'DEPLOYMENT_MODE', None)):
            if attrs.get('role') == 'Developer':
                raise serializers.ValidationError(
                    {'role': 'Developer role is not available in this deployment.'}
                )
        
        return attrs
    
    def validate_email(self, value):
        """Validate email is unique"""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        return User.objects.create_user(password=password, **validated_data)


class LoginSerializer(serializers.Serializer):
    """Serializer for user login with security enhancements"""
    username = serializers.CharField(required=True, max_length=150)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    
    def validate_username(self, value):
        """Validate and sanitize username or email"""
        if not value:
            raise serializers.ValidationError('Please enter your username or email.')
        
        # Limit length to prevent DoS
        if len(value) > 150:
            raise serializers.ValidationError('Username or email is too long (maximum 150 characters).')
        
        return value.strip().lower()
    
    def validate(self, attrs):
        """Validate credentials"""
        username = attrs.get('username')  # Already lowercased in validate_username
        password = attrs.get('password')
        
        if not username or not password:
            raise serializers.ValidationError({
                'non_field_errors': ['Please enter your username or email and password.']
            })
        
        # Try to find user by username (case-insensitive) or email
        user = None
        user_obj = None
        try:
            from .models import User
            
            # Try username (case-insensitive match)
            user_obj = User.objects.filter(username__iexact=username).first()
            if user_obj:
                logger.info(f'Found user by username: "{user_obj.username}" (requested: "{username}"), is_active: {user_obj.is_active}')
                
                # First try Django's authenticate (uses AUTHENTICATION_BACKENDS)
                user = authenticate(username=user_obj.username, password=password)
                
                # If authenticate fails, try manual password check as fallback
                if not user and user_obj.check_password(password):
                    logger.info(f'Password check passed manually for username: "{user_obj.username}"')
                    user = user_obj
                elif not user:
                    logger.warning(f'Authentication failed for username: "{user_obj.username}". Password check failed.')
                    # Log additional debug info (without exposing password)
                    logger.debug(f'User object details - username: "{user_obj.username}", email: "{user_obj.email}", is_active: {user_obj.is_active}, is_staff: {user_obj.is_staff}, has_usable_password: {user_obj.has_usable_password()}')
                else:
                    logger.info(f'Authentication successful for username: "{user_obj.username}"')
            
            # If username auth failed, try email
            if not user:
                user_obj = User.objects.filter(email__iexact=username).first()
                if user_obj:
                    logger.info(f'Found user by email: "{user_obj.email}", username: "{user_obj.username}", is_active: {user_obj.is_active}')
                    
                    # First try Django's authenticate
                    user = authenticate(username=user_obj.username, password=password)
                    
                    # If authenticate fails, try manual password check as fallback
                    if not user and user_obj.check_password(password):
                        logger.info(f'Password check passed manually for email: "{user_obj.email}"')
                        user = user_obj
                    elif not user:
                        logger.warning(f'Authentication failed for email: "{user_obj.email}". Password check failed.')
                    else:
                        logger.info(f'Authentication successful for email: "{user_obj.email}"')
            
            if not user_obj:
                logger.warning(f'No user found with username/email: "{username}"')
        except Exception as e:
            logger.error(f'Authentication error: {e}', exc_info=True)
            pass
        
        if not user:
            # Don't reveal whether user exists (prevent enumeration)
            raise serializers.ValidationError({
                'non_field_errors': ['Unable to log in with provided credentials.']
            })
        
        if not user.is_active:
            raise serializers.ValidationError({
                'non_field_errors': ['User account is disabled.']
            })
        
        attrs['user'] = user
        return attrs


class RoleSerializer(serializers.Serializer):
    """Serializer for role management"""
    ROLE_CHOICES = [
        ('Developer', 'Developer'),
        ('Manager', 'Manager'),
        ('Employee', 'Employee'),
        ('Visitor', 'Visitor'),
    ]
    ROLE_CHOICES_CLIENT = [
        ('Manager', 'Manager'),
        ('Employee', 'Employee'),
        ('Visitor', 'Visitor'),
    ]

    role = serializers.ChoiceField(choices=ROLE_CHOICES)
    description = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if is_client_deployment(getattr(settings, 'DEPLOYMENT_MODE', None)):
            self.fields['role'] = serializers.ChoiceField(choices=self.ROLE_CHOICES_CLIENT)

    def get_description(self, role):
        """Get role description"""
        descriptions = {
            'Developer': 'Full system access including settings, logs, and license management',
            'Manager': 'Manage team (Employees), screens, and content; no system-level settings',
            'Employee': 'Screens, playlists, templates, content, commands, logs, analytics, and settings for your organization',
            'Visitor': 'Dashboard and template exploration; changes are not saved',
        }
        return descriptions.get(role, '')


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate_new_password(self, value):
        """Validate new password strength"""
        if not value:
            raise serializers.ValidationError("New password is required.")
        
        # Check password strength
        from .security import PasswordStrengthChecker
        strength = PasswordStrengthChecker.check_password_strength(value)
        
        if strength['score'] < 2:
            raise serializers.ValidationError(
                f"Password is too weak. {', '.join(strength['feedback'][:2])}"
            )
        
        return value
    
    def validate(self, attrs):
        """Validate password change"""
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        if new_password != new_password_confirm:
            raise serializers.ValidationError({"new_password_confirm": "Password fields didn't match."})
        
        # Ensure new password is different from old password
        old_password = attrs.get('old_password')
        if old_password and new_password == old_password:
            raise serializers.ValidationError({"new_password": "New password must be different from old password."})
        
        return attrs
    
    def validate_old_password(self, value):
        """Validate old password"""
        if not value:
            raise serializers.ValidationError("Old password is required.")
        
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        
        return value


class ScreenGramTokenObtainPairSerializer(TokenObtainPairSerializer):
    token_class = ScreenGramRefreshToken

    def validate(self, attrs):
        data = super().validate(attrs)
        from saas_platform.tenant_assignment import ensure_user_tenant

        ensure_user_tenant(self.user)
        return data


class ScreenGramTokenRefreshSerializer(TokenRefreshSerializer):
    token_class = ScreenGramRefreshToken

    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh"])

        user_id = refresh.payload.get(jwt_api_settings.USER_ID_CLAIM, None)
        if user_id and (
            user := get_user_model().objects.get(
                **{jwt_api_settings.USER_ID_FIELD: user_id}
            )
        ):
            if not jwt_api_settings.USER_AUTHENTICATION_RULE(user):
                raise AuthenticationFailed(
                    self.error_messages["no_active_account"],
                    "no_active_account",
                )
            refresh["role"] = user.role

        data = {"access": str(refresh.access_token)}

        if jwt_api_settings.ROTATE_REFRESH_TOKENS:
            if jwt_api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    refresh.blacklist()
                except AttributeError:
                    pass

            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()
            refresh.outstand()

            data["refresh"] = str(refresh)

        return data
