"""
Views for setup/installation API endpoints.

Security: These endpoints are ONLY accessible if installed.lock does NOT exist.
"""
import logging
import os
from django.db import connection
from django.db.models import Q
from django.db.utils import OperationalError, DatabaseError
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.management.utils import get_random_secret_key
from django.conf import settings
from io import StringIO
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import (
    DBCredentialsSerializer,
    DBCheckSerializer,
    RunMigrationsSerializer,
    SeedAssetsSerializer,
    CreateAdminSerializer,
    FinalizeSerializer,
    SetupStatusSerializer
)
from core.deployment import is_client_deployment
from .client_install import create_or_get_client_tenant
from .utils import is_installed, mark_as_installed
from .env_manager import finalize_installation, EnvManagerError

User = get_user_model()
logger = logging.getLogger(__name__)


def check_setup_allowed():
    """
    Security check: Setup endpoints are ONLY accessible if installation is NOT completed.
    
    Returns:
        tuple: (allowed: bool, error_response: Response or None)
    """
    if is_installed():
        return False, Response({
            'error': 'installation_completed',
            'message': 'Installation has already been completed. Setup endpoints are no longer accessible.'
        }, status=status.HTTP_403_FORBIDDEN)
    return True, None


@api_view(['GET'])
@permission_classes([AllowAny])
def setup_status(request):
    """
    Get the current setup status.
    """
    try:
        # Check database connection
        db_connected = False
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_connected = True
        except (OperationalError, DatabaseError):
            db_connected = False
        
        # Check if migrations are applied (check if User table exists)
        migrations_applied = False
        try:
            User.objects.exists()
            migrations_applied = True
        except Exception:
            migrations_applied = False
        
        # Check if admin exists
        admin_exists = False
        try:
            admin_exists = User.objects.filter(is_superuser=True).exists()
        except Exception:
            admin_exists = False
        
        raw_pwd = settings.DATABASES['default'].get('PASSWORD') or ''
        serializer = SetupStatusSerializer({
            'installed': is_installed(),
            'database_connected': db_connected,
            'migrations_applied': migrations_applied,
            'admin_exists': admin_exists,
            'db_name': settings.DATABASES['default'].get('NAME', 'pixelcast_signage_db'),
            'db_user': settings.DATABASES['default'].get('USER', 'pixelcast_signage_user'),
            'db_password_configured': bool(str(raw_pwd).strip()),
            'db_host': settings.DATABASES['default'].get('HOST', 'db'),
            'db_port': str(settings.DATABASES['default'].get('PORT', '5432')),
        })
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error checking setup status: {str(e)}", exc_info=True)
        return Response({
            'error': 'status_check_failed',
            'message': f'Failed to check setup status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def db_check(request):
    """
    Test database connection with provided credentials.
    
    Security: Only accessible if installation is not completed.
    """
    # Security check
    allowed, error_response = check_setup_allowed()
    if not allowed:
        return error_response
    
    serializer = DBCredentialsSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'error': 'validation_error',
            'message': 'Invalid database credentials provided.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get validated credentials (empty password => use username as password)
        db_name = serializer.validated_data['name']
        db_user = serializer.validated_data['user']
        db_password = (serializer.validated_data.get('password') or '').strip() or db_user
        db_host = serializer.validated_data.get('host', 'localhost')
        db_port = serializer.validated_data.get('port', 5432)
        
        # Test connection using psycopg2 directly
        import psycopg2

        def try_connect(password):
            return psycopg2.connect(
                dbname=db_name,
                user=db_user,
                password=password,
                host=db_host,
                port=db_port,
                connect_timeout=10
            )
        
        try:
            # Create test connection (with optional retry using username-as-password)
            conn = try_connect(db_password)
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()[0]
                    cursor.execute("SELECT current_database()")
                    current_db = cursor.fetchone()[0]

                db_info = {
                    'vendor': 'postgresql',
                    'version': version.split(',')[0] if version else 'unknown',
                    'database': current_db,
                    'host': db_host,
                    'port': db_port,
                }

                serializer = DBCheckSerializer({
                    'status': 'success',
                    'message': 'Database connection successful',
                    'details': db_info
                })

                return Response(serializer.data, status=status.HTTP_200_OK)
            finally:
                conn.close()
        except psycopg2.OperationalError as e:
            # If auth failed and we haven't already tried username-as-password, retry once
            err_msg = str(e).lower()
            if ('password authentication failed' in err_msg or 'authentication failed' in err_msg) and db_password != db_user:
                try:
                    conn = try_connect(db_user)
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute("SELECT version()")
                            version = cursor.fetchone()[0]
                            cursor.execute("SELECT current_database()")
                            current_db = cursor.fetchone()[0]
                        db_info = {
                            'vendor': 'postgresql',
                            'version': version.split(',')[0] if version else 'unknown',
                            'database': current_db,
                            'host': db_host,
                            'port': db_port,
                        }
                        serializer = DBCheckSerializer({
                            'status': 'success',
                            'message': 'Database connection successful (using username as password)',
                            'details': db_info
                        })
                        return Response(serializer.data, status=status.HTTP_200_OK)
                    finally:
                        conn.close()
                except Exception:
                    pass
            raise  # Re-raise to be caught by outer handler
        except Exception:
            raise  # Re-raise to be caught by outer handler

    except OperationalError as e:
        logger.error(f"Database connection failed: {str(e)}", exc_info=True)
        serializer = DBCheckSerializer({
            'status': 'error',
            'message': f'Database connection failed: {str(e)}',
            'details': {}
        })
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error testing database connection: {str(e)}", exc_info=True)
        serializer = DBCheckSerializer({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}',
            'details': {}
        })
        return Response(serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def run_migrations(request):
    """
    Run database migrations programmatically.
    
    Security: Only accessible if installation is not completed.
    """
    # Security check
    allowed, error_response = check_setup_allowed()
    if not allowed:
        return error_response
    
    try:
        output = StringIO()
        call_command('migrate', verbosity=2, stdout=output, no_input=True)
        output_str = output.getvalue()
        
        # Extract applied migrations from output
        applied_migrations = []
        for line in output_str.split('\n'):
            if 'Applying' in line or 'Apply' in line:
                applied_migrations.append(line.strip())
        
        serializer = RunMigrationsSerializer({
            'status': 'success',
            'message': 'Migrations applied successfully',
            'applied_migrations': applied_migrations if applied_migrations else ['All migrations up to date']
        })
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    except CommandError as e:
        logger.error(f"Migration failed: {str(e)}", exc_info=True)
        serializer = RunMigrationsSerializer({
            'status': 'error',
            'message': f'Migration failed: {str(e)}',
            'applied_migrations': []
        })
        return Response(serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}", exc_info=True)
        serializer = RunMigrationsSerializer({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}',
            'applied_migrations': []
        })
        return Response(serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def seed_assets(request):
    """
    Seed default notification events and related system assets.

    Security: Only accessible if installation is not completed.
    """
    allowed, error_response = check_setup_allowed()
    if not allowed:
        return error_response

    try:
        out = StringIO()
        err = StringIO()
        call_command('init_notification_events', stdout=out, stderr=err, no_color=True)
        msg = (out.getvalue() or '').strip() or 'Notification events initialized'
        serializer = SeedAssetsSerializer({
            'status': 'success',
            'message': msg,
        })
        return Response(serializer.data, status=status.HTTP_200_OK)
    except CommandError as e:
        logger.error(f"Seed assets failed: {str(e)}", exc_info=True)
        serializer = SeedAssetsSerializer({
            'status': 'error',
            'message': f'Seed assets failed: {str(e)}',
        })
        return Response(serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Error seeding assets: {str(e)}", exc_info=True)
        serializer = SeedAssetsSerializer({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}',
        })
        return Response(serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_admin(request):
    """
    Create or update the admin (superuser) account (upsert).
    If a user with the given username or email exists, update their password and profile.
    Security: Only accessible if installation is not completed.
    """
    # Security check
    allowed, error_response = check_setup_allowed()
    if not allowed:
        return error_response
    
    serializer = CreateAdminSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'error': 'validation_error',
            'message': 'Invalid admin credentials provided.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        username = serializer.validated_data['username']
        raw_password = (serializer.validated_data.get('password') or '').strip()
        password = raw_password or username  # Fallback: use username as password if empty
        email = serializer.validated_data['email']
        first_name = serializer.validated_data.get('first_name', '')
        last_name = serializer.validated_data.get('last_name', '')
        org = (serializer.validated_data.get('organization_name') or '').strip()
        is_client = is_client_deployment(getattr(settings, 'DEPLOYMENT_MODE', None))
        if is_client and not org:
            return Response(
                {
                    'error': 'validation_error',
                    'message': 'organization_name is required for client deployment.',
                    'errors': {'organization_name': ['This field is required.']},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Upsert: find existing user by username or email
        existing = User.objects.filter(
            Q(username=username) | Q(email=email)
        ).first()
        
        if existing:
            # Update existing user so submitted credentials become the active ones
            existing.email = email
            existing.first_name = first_name
            existing.last_name = last_name
            existing.is_superuser = True
            existing.is_staff = True
            existing.role = 'Manager' if is_client else 'Developer'
            existing.set_password(password)
            if is_client:
                tenant = create_or_get_client_tenant(org)
                existing.organization_name = org
                existing.tenant = tenant
            existing.save()  # full save so hashed password is persisted
            user = existing
            created = False
            logger.info(f"Admin user updated: {username}")
        else:
            # Single create: staff + superuser; client uses Manager + fixed tenant
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='Manager' if is_client else 'Developer',
                is_staff=True,
                is_superuser=True,
            )
            if is_client:
                tenant = create_or_get_client_tenant(org)
                user.organization_name = org
                user.tenant = tenant
                user.save(update_fields=['organization_name', 'tenant'])
            created = True
            logger.info(f"Admin user created: {username}")
        
        return Response({
            'status': 'success',
            'message': f'Admin user "{username}" updated successfully' if not created else f'Admin user "{username}" created successfully',
            'created': created,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error creating/updating admin user: {str(e)}", exc_info=True)
        return Response({
            'error': 'creation_failed',
            'message': f'Failed to create or update admin user: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def finalize(request):
    """
    Finalize installation by saving environment configuration and creating installed.lock file.
    Optionally attempts to restart Gunicorn if possible.
    
    Security: Only accessible if installation is not completed.
    """
    # Security check
    allowed, error_response = check_setup_allowed()
    if not allowed:
        return error_response
    
    serializer = FinalizeSerializer(data=request.data)
    
    # Initialize env_data dictionary
    env_data = {}
    
    # Validate serializer (but allow partial data)
    if serializer.is_valid(raise_exception=False):
        # Extract environment variables from request
        if serializer.validated_data.get('db_name'):
            env_data['DB_NAME'] = serializer.validated_data['db_name']
        if serializer.validated_data.get('db_user'):
            env_data['DB_USER'] = serializer.validated_data['db_user']
        # DB_PASSWORD: use submitted password, or fall back to username (auto-fix)
        raw_password = (serializer.validated_data.get('db_password') or '').strip()
        if serializer.validated_data.get('db_user'):
            env_data['DB_PASSWORD'] = raw_password or serializer.validated_data['db_user']
        elif raw_password:
            env_data['DB_PASSWORD'] = raw_password
        if serializer.validated_data.get('db_host'):
            env_data['DB_HOST'] = serializer.validated_data['db_host']
        if serializer.validated_data.get('db_port') is not None:
            env_data['DB_PORT'] = str(serializer.validated_data['db_port'])
        if serializer.validated_data.get('secret_key'):
            env_data['SECRET_KEY'] = serializer.validated_data['secret_key']
        if serializer.validated_data.get('base_url'):
            env_data['BASE_URL'] = serializer.validated_data['base_url']
        if 'debug' in serializer.validated_data:
            env_data['DEBUG'] = str(serializer.validated_data['debug'])
        if serializer.validated_data.get('allowed_hosts'):
            env_data['ALLOWED_HOSTS'] = serializer.validated_data['allowed_hosts']
    
    # Get current database settings from Django settings (if not provided)
    if not env_data.get('DB_NAME'):
        env_data['DB_NAME'] = settings.DATABASES['default'].get('NAME', 'pixelcast_signage_db')
    if not env_data.get('DB_USER'):
        env_data['DB_USER'] = settings.DATABASES['default'].get('USER', 'pixelcast_signage_user')
    if not env_data.get('DB_PASSWORD') or not str(env_data.get('DB_PASSWORD', '')).strip():
        # Auto-fix: use DB_USER as DB_PASSWORD when password is missing/empty
        env_data['DB_PASSWORD'] = env_data.get('DB_USER', 'pixelcast_signage_user')
    if not env_data.get('DB_HOST'):
        env_data['DB_HOST'] = settings.DATABASES['default'].get('HOST', 'db')
    if not env_data.get('DB_PORT'):
        env_data['DB_PORT'] = str(settings.DATABASES['default'].get('PORT', '5432'))
    # Docker Postgres: same password for POSTGRES_PASSWORD
    env_data['POSTGRES_PASSWORD'] = env_data['DB_PASSWORD']
    
    # Get SECRET_KEY from settings if not provided.
    # Ensure wizard never fails with too-short defaults.
    if not env_data.get('SECRET_KEY'):
        configured_secret = str(getattr(settings, 'SECRET_KEY', '') or '').strip()
        env_data['SECRET_KEY'] = configured_secret if len(configured_secret) >= 50 else get_random_secret_key()
    
    # Get BASE_URL if not provided
    if not env_data.get('BASE_URL'):
        env_data['BASE_URL'] = getattr(settings, 'BASE_URL', 'http://localhost')
    
    # Set defaults
    if 'DEBUG' not in env_data:
        env_data['DEBUG'] = str(getattr(settings, 'DEBUG', False))
    if 'ALLOWED_HOSTS' not in env_data:
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        env_data['ALLOWED_HOSTS'] = ','.join(allowed_hosts) if allowed_hosts else 'localhost,127.0.0.1'

    # Pixelcast client build: single-tenant mode written to .env on finalize
    env_data['DEPLOYMENT_MODE'] = 'client'
    
    try:
        # Verify prerequisites before finalizing
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except (OperationalError, DatabaseError):
            return Response({
                'error': 'database_not_connected',
                'message': 'Database connection is not established. Please test the database connection first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if migrations are applied
        try:
            User.objects.exists()
        except Exception:
            return Response({
                'error': 'migrations_not_applied',
                'message': 'Database migrations are not applied. Please run migrations first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if admin exists
        if not User.objects.filter(is_superuser=True).exists():
            return Response({
                'error': 'admin_not_created',
                'message': 'Admin user has not been created. Please create an admin user first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save environment configuration and create installed.lock
        if env_data:
            try:
                success, error_msg = finalize_installation(env_data)
                if not success:
                    return Response({
                        'error': 'env_file_creation_failed',
                        'message': f'Failed to create .env file: {error_msg}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                logger.info("Environment configuration saved successfully")
            except EnvManagerError as e:
                logger.error(f"EnvManager error: {str(e)}", exc_info=True)
                return Response({
                    'error': 'env_manager_error',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Just create installed.lock if no env data provided
            if not mark_as_installed():
                return Response({
                    'error': 'lock_file_creation_failed',
                    'message': 'Failed to create installed.lock file.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            logger.info("Installation lock file created (no env data provided)")
        
        # Attempt to restart Gunicorn if possible
        restart_required = False
        restart_message = None
        
        try:
            # Check if we're running under Gunicorn
            import os
            if 'gunicorn' in os.environ.get('SERVER_SOFTWARE', '').lower():
                # Try to send HUP signal to Gunicorn master process
                # This requires the process to have permission to send signals
                try:
                    import signal
                    # Get parent process (Gunicorn master)
                    parent_pid = os.getppid()
                    os.kill(parent_pid, signal.SIGHUP)
                    restart_message = 'Gunicorn restart signal sent'
                except (PermissionError, ProcessLookupError, AttributeError):
                    restart_required = True
                    restart_message = 'Manual restart required: Please restart Gunicorn manually'
            else:
                restart_required = True
                restart_message = 'Manual restart may be required'
        except Exception as e:
            logger.warning(f"Could not restart Gunicorn: {str(e)}")
            restart_required = True
            restart_message = 'Manual restart may be required'
        
        serializer = FinalizeSerializer({
            'status': 'success',
            'message': 'Installation finalized successfully. You can now access the application.',
            'restart_required': restart_required
        })
        
        response_data = serializer.data
        if restart_message:
            response_data['restart_message'] = restart_message
        
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error finalizing installation: {str(e)}", exc_info=True)
        return Response({
            'error': 'finalization_failed',
            'message': f'Failed to finalize installation: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
