from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    UserViewSet,
    login_view,
    logout_view,
    logout_all_view,
    sessions_view,
    signup_view,
    roles_view,
    create_role,
    SendVerificationEmail,
    VerifyEmail,
    sidebar_items_view,
)
from .invite_views import accept_invitation, team_invitations
from .sso_views import sso_account_link_status, sso_providers_public
from .api_auth_extras import (
    login_2fa_view,
    password_reset_confirm_view,
    password_reset_request_view,
    revoke_session_view,
    twofa_disable_view,
    twofa_setup_confirm_view,
    twofa_setup_start_view,
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Router URLs (includes /api/users/ for ViewSet)
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('auth/signup/', signup_view, name='auth-signup'),
    path('auth/login/', login_view, name='auth-login'),
    path('auth/login/2fa/', login_2fa_view, name='auth-login-2fa'),
    path('auth/password-reset/request/', password_reset_request_view, name='auth-password-reset-request'),
    path('auth/password-reset/confirm/', password_reset_confirm_view, name='auth-password-reset-confirm'),
    path('auth/2fa/setup/start/', twofa_setup_start_view, name='auth-2fa-setup-start'),
    path('auth/2fa/setup/confirm/', twofa_setup_confirm_view, name='auth-2fa-setup-confirm'),
    path('auth/2fa/disable/', twofa_disable_view, name='auth-2fa-disable'),
    path('auth/sessions/revoke/', revoke_session_view, name='auth-sessions-revoke'),
    path('auth/logout/', logout_view, name='auth-logout'),
    path('auth/logout-all/', logout_all_view, name='auth-logout-all'),
    path('auth/sessions/', sessions_view, name='auth-sessions'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Role management endpoints
    path('roles/', roles_view, name='roles-list'),
    path('roles/create/', create_role, name='roles-create'),
    
    # Email verification endpoints
    path('send-verification-email/', SendVerificationEmail.as_view(), name='send-verification-email'),
    path('verify-email/', VerifyEmail.as_view(), name='verify-email'),
    
    # Sidebar items endpoint
    path('sidebar-items/', sidebar_items_view, name='sidebar-items'),

    # Team / SSO
    path('team/invitations/', team_invitations, name='team-invitations'),
    path('team/invitations/accept/', accept_invitation, name='team-invitations-accept'),
    path('auth/sso/providers/', sso_providers_public, name='auth-sso-providers'),
    path('auth/sso/status/', sso_account_link_status, name='auth-sso-status'),
]
