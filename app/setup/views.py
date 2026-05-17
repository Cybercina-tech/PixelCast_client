"""
Views for setup/installation API endpoints.

Security: These endpoints are ONLY accessible if installed.lock does NOT exist.
"""
import logging
import os
from django.db import connection
from django.db import connections
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
    InstallSerializer,
    RunMigrationsSerializer,
    SeedAssetsSerializer,
    CreateAdminSerializer,
    FinalizeSerializer,
    SetupStatusSerializer
)
from core.deployment import is_client_deployment
from .client_install import create_or_get_client_tenant
from .utils import is_installed, mark_as_installed
from .env_manager import finalize_installation, update_env_file, EnvManagerError
from licensing.client import (
    LicenseServerError,
    license_gateway_base_url,
    license_validate_url,
    post_gateway_activate,
    post_license_validation,
)
from licensing.service import PURCHASE_CODE_RE, activate_license

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


def _get_request_domain_and_base_url(request, submitted_domain: str = "", submitted_base_url: str = ""):
    host = (submitted_domain or "").strip()
    if not host:
        host = request.get_host().strip()
    host = host.split(":")[0].strip().lower()
    if not host:
        host = "localhost"
    base_url = (submitted_base_url or "").strip()
    if not base_url:
        base_url = f"{request.scheme}://{host}"
    return host, base_url


def _normalize_csv_hosts(csv_value: str, default_host: str) -> str:
    hosts = [h.strip().lower() for h in str(csv_value or "").split(",") if h.strip()]
    if default_host not in hosts:
        hosts.append(default_host)
    for local in ("localhost", "127.0.0.1"):
        if local not in hosts:
            hosts.append(local)
    # Stable order + de-dup
    return ",".join(dict.fromkeys(hosts))


def _normalize_csv_origins(csv_value: str, default_origin: str) -> str:
    origins = [o.strip() for o in str(csv_value or "").split(",") if o.strip()]
    if default_origin not in origins:
        origins.append(default_origin)
    return ",".join(dict.fromkeys(origins))


def _build_env_data_from_install_payload(payload: dict, host: str, base_url: str) -> dict:
    raw_db_password = (payload.get("db_password") or "").strip()
    db_password = raw_db_password or payload["db_user"]
    allowed_hosts = _normalize_csv_hosts(payload.get("allowed_hosts"), host)
    cors_origins = _normalize_csv_origins(payload.get("cors_allowed_origins"), base_url)

    configured_secret = str(getattr(settings, "SECRET_KEY", "") or "").strip()
    secret_key = configured_secret if len(configured_secret) >= 50 else get_random_secret_key()

    return {
        "DB_NAME": payload["db_name"],
        "DB_USER": payload["db_user"],
        "DB_PASSWORD": db_password,
        "POSTGRES_PASSWORD": db_password,
        "DB_HOST": payload.get("db_host") or "localhost",
        "DB_PORT": str(payload.get("db_port") or 5432),
        "SECRET_KEY": secret_key,
        "BASE_URL": base_url,
        "ALLOWED_HOSTS": allowed_hosts,
        "CORS_ALLOWED_ORIGINS": cors_origins,
        "CSRF_TRUSTED_ORIGINS": cors_origins,
        "DEBUG": str(bool(payload.get("debug", False))),
        "DEPLOYMENT_MODE": "client",
        "PURCHASE_CODE": payload["purchase_code"].strip(),
    }


def _test_postgres_connection(db_name: str, db_user: str, db_password: str, db_host: str, db_port: int):
    import psycopg2

    def try_connect(password):
        return psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=password,
            host=db_host,
            port=db_port,
            connect_timeout=10,
        )

    try:
        conn = try_connect(db_password)
    except psycopg2.OperationalError as e:
        err_msg = str(e).lower()
        if ("password authentication failed" in err_msg or "authentication failed" in err_msg) and db_password != db_user:
            conn = try_connect(db_user)
        else:
            raise

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            cursor.execute("SELECT current_database()")
            current_db = cursor.fetchone()[0]
        return {
            "vendor": "postgresql",
            "version": version.split(",")[0] if version else "unknown",
            "database": current_db,
            "host": db_host,
            "port": db_port,
        }
    finally:
        conn.close()


def _apply_runtime_database_settings(db_name: str, db_user: str, db_password: str, db_host: str, db_port: int):
    settings.DATABASES["default"]["ENGINE"] = "django.db.backends.postgresql"
    settings.DATABASES["default"]["NAME"] = db_name
    settings.DATABASES["default"]["USER"] = db_user
    settings.DATABASES["default"]["PASSWORD"] = db_password
    settings.DATABASES["default"]["HOST"] = db_host
    settings.DATABASES["default"]["PORT"] = str(db_port)
    settings.DATABASES["default"].setdefault("OPTIONS", {})["connect_timeout"] = 10
    connections.close_all()


def _preflight_validate_purchase_code(purchase_code: str, domain: str):
    code = (purchase_code or "").strip()
    if not PURCHASE_CODE_RE.match(code):
        raise ValueError("Purchase code format is invalid")

    base = license_gateway_base_url()
    if base:
        payload = {
            "purchase_code": code,
            "domain": domain or "",
            "product_id": (getattr(settings, "CODECANYON_PRODUCT_ID", "") or "").strip(),
            "app_version": (getattr(settings, "SCREENGRAM_APP_VERSION", "") or "").strip(),
        }
        data = post_gateway_activate(base, payload)
        token = (data.get("activation_token") or "").strip()
        if not token:
            raise ValueError(data.get("message") or "License activation token was not returned")
        return

    validation_url = license_validate_url()
    if not validation_url:
        raise ValueError("License server URL is not configured")

    is_valid, data = post_license_validation(
        license_server_url=validation_url,
        payload={
            "purchase_code": code,
            "product_id": (getattr(settings, "CODECANYON_PRODUCT_ID", "") or "").strip(),
            "domain": domain or "",
        },
        token=(getattr(settings, "CODECANYON_TOKEN", "") or "").strip(),
        timeout_seconds=int(getattr(settings, "LICENSE_SERVER_TIMEOUT_SECONDS", 8)),
    )
    if not is_valid:
        raise ValueError(data.get("message") or "Purchase code is invalid")


def _upsert_admin_user(payload: dict):
    username = payload["admin_username"]
    email = payload["admin_email"]
    password = payload["admin_password"]
    first_name = payload.get("admin_first_name", "")
    last_name = payload.get("admin_last_name", "")
    org = (payload.get("organization_name") or "").strip()
    is_client = is_client_deployment(getattr(settings, "DEPLOYMENT_MODE", None))
    if is_client and not org:
        raise ValueError("organization_name is required for client deployment")

    existing = User.objects.filter(Q(username=username) | Q(email=email)).first()
    if existing:
        existing.email = email
        existing.first_name = first_name
        existing.last_name = last_name
        existing.is_superuser = True
        existing.is_staff = True
        existing.role = "Manager" if is_client else "Developer"
        existing.set_password(password)
        if is_client:
            tenant = create_or_get_client_tenant(org)
            existing.organization_name = org
            existing.tenant = tenant
        existing.save()
        return existing, False

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role="Manager" if is_client else "Developer",
        is_staff=True,
        is_superuser=True,
    )
    if is_client:
        tenant = create_or_get_client_tenant(org)
        user.organization_name = org
        user.tenant = tenant
        user.save(update_fields=["organization_name", "tenant"])
    return user, True


def _touch_passenger_restart_file():
    restart_file = os.path.join(settings.BASE_DIR, "tmp", "restart.txt")
    os.makedirs(os.path.dirname(restart_file), exist_ok=True)
    with open(restart_file, "a", encoding="utf-8"):
        os.utime(restart_file, None)
    return restart_file


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
        detected_host = request.get_host().split(':')[0].strip().lower()
        serializer = SetupStatusSerializer({
            'installed': is_installed(),
            'database_connected': db_connected,
            'migrations_applied': migrations_applied,
            'admin_exists': admin_exists,
            'detected_host': detected_host,
            'detected_base_url': f'{request.scheme}://{detected_host}' if detected_host else '',
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
        db_info = _test_postgres_connection(
            db_name=db_name,
            db_user=db_user,
            db_password=db_password,
            db_host=db_host,
            db_port=db_port,
        )

        serializer = DBCheckSerializer({
            'status': 'success',
            'message': 'Database connection successful',
            'details': db_info
        })

        return Response(serializer.data, status=status.HTTP_200_OK)

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
def install(request):
    """
    One-shot installation flow for shared hosting:
    license preflight -> env write -> migrate -> seed -> admin -> persist license -> lock -> restart marker.
    """
    allowed, error_response = check_setup_allowed()
    if not allowed:
        return error_response

    serializer = InstallSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                'error': 'validation_error',
                'message': 'Invalid installation payload.',
                'errors': serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    payload = serializer.validated_data
    host, base_url = _get_request_domain_and_base_url(
        request,
        submitted_domain=payload.get('domain', ''),
        submitted_base_url=payload.get('base_url', ''),
    )

    db_password = (payload.get('db_password') or '').strip() or payload['db_user']

    # 1) Validate DB before any side effects.
    try:
        _test_postgres_connection(
            db_name=payload['db_name'],
            db_user=payload['db_user'],
            db_password=db_password,
            db_host=payload.get('db_host', 'localhost'),
            db_port=payload.get('db_port', 5432),
        )
    except Exception as exc:
        logger.error("Install DB validation failed: %s", exc, exc_info=True)
        return Response(
            {
                'error': 'database_connection_failed',
                'message': f'Database connection failed: {exc}',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 2) Validate purchase code before writing .env or migrating.
    try:
        _preflight_validate_purchase_code(payload['purchase_code'], host)
    except (ValueError, LicenseServerError) as exc:
        logger.warning("Install license validation failed: %s", exc)
        status_code = status.HTTP_429_TOO_MANY_REQUESTS if getattr(exc, 'status_code', None) == 429 else status.HTTP_400_BAD_REQUEST
        return Response(
            {
                'error': 'license_validation_failed',
                'message': str(exc),
                'retry_after': getattr(exc, 'retry_after', None),
            },
            status=status_code,
        )

    env_data = _build_env_data_from_install_payload(payload, host=host, base_url=base_url)

    # 3) Persist .env (atomic in env_manager).
    ok, env_error = update_env_file(env_data)
    if not ok:
        return Response(
            {
                'error': 'env_file_creation_failed',
                'message': env_error or 'Failed to update .env file.',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # 4) Switch current runtime DB config to submitted DB then migrate/seed/admin.
    try:
        _apply_runtime_database_settings(
            db_name=payload['db_name'],
            db_user=payload['db_user'],
            db_password=db_password,
            db_host=payload.get('db_host', 'localhost'),
            db_port=payload.get('db_port', 5432),
        )
        call_command('migrate', verbosity=1, interactive=False)
        call_command('init_notification_events', no_color=True)
        admin_user, admin_created = _upsert_admin_user(payload)
    except Exception as exc:
        logger.error("Install migration/admin step failed: %s", exc, exc_info=True)
        return Response(
            {
                'error': 'install_execution_failed',
                'message': f'Install failed after environment save: {exc}',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # 5) Persist license state after licensing tables exist.
    try:
        decision = activate_license(payload['purchase_code'], domain=host)
        if not decision.allow:
            return Response(
                {
                    'error': decision.error_code or 'license_activation_failed',
                    'message': decision.message,
                    'license_status': decision.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as exc:
        logger.error("Install license activation persistence failed: %s", exc, exc_info=True)
        return Response(
            {
                'error': 'license_activation_failed',
                'message': str(exc),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # 6) Mark installed and request passenger restart.
    if not mark_as_installed():
        return Response(
            {
                'error': 'lock_file_creation_failed',
                'message': 'Failed to create installed.lock file.',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    restart_file = None
    try:
        restart_file = _touch_passenger_restart_file()
    except Exception as exc:
        logger.warning("Install completed but restart marker failed: %s", exc)

    return Response(
        {
            'status': 'success',
            'message': 'Installation completed successfully.',
            'admin_created': admin_created,
            'admin_user': {
                'id': admin_user.id,
                'username': admin_user.username,
                'email': admin_user.email,
            },
            'restart_file': restart_file,
            'restart_required': True,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def restart_application(request):
    """
    Touch tmp/restart.txt to trigger Phusion Passenger restart on cPanel.
    """
    allowed, error_response = check_setup_allowed()
    if not allowed:
        return error_response

    try:
        restart_file = _touch_passenger_restart_file()
        return Response(
            {
                'status': 'success',
                'message': 'Restart signal created successfully.',
                'restart_file': restart_file,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as exc:
        logger.error("Failed to touch Passenger restart marker: %s", exc, exc_info=True)
        return Response(
            {
                'error': 'restart_failed',
                'message': str(exc),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


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
        
        # cPanel/Passenger restart signal (tmp/restart.txt)
        restart_required = False
        restart_message = None

        try:
            restart_file = _touch_passenger_restart_file()
            restart_required = True
            restart_message = f'Passenger restart signal written to {restart_file}'
        except Exception as e:
            logger.warning(f"Could not touch Passenger restart marker: {str(e)}")
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
