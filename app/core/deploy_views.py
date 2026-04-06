"""
Deployment webhook views for automated GitHub deployments.

This module handles GitHub webhook requests to trigger automated deployments.
"""

import os
import subprocess
import hmac
import hashlib
import json
import logging
import secrets
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def verify_github_signature(payload_body, signature_header):
    """
    Verify GitHub webhook signature.
    
    Args:
        payload_body: Raw request body (bytes)
        signature_header: X-Hub-Signature-256 header value
    
    Returns:
        bool: True if signature is valid
    """
    if not signature_header:
        return False
    
    # Get secret token from settings
    secret_token = os.environ.get('GITHUB_WEBHOOK_SECRET', '')
    if not secret_token:
        logger.warning("GITHUB_WEBHOOK_SECRET is not set. Webhook verification disabled.")
        return False
    
    # GitHub sends signature as "sha256=<hash>"
    if not signature_header.startswith('sha256='):
        return False
    
    # Extract hash
    received_hash = signature_header.split('sha256=')[1]
    
    # Calculate expected hash
    expected_hash = hmac.new(
        secret_token.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare hashes (constant-time comparison)
    return hmac.compare_digest(received_hash, expected_hash)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
@require_POST
def github_webhook(request):
    """
    GitHub webhook endpoint for automated deployments.
    
    This endpoint:
    1. Verifies the webhook signature using GITHUB_WEBHOOK_SECRET
    2. Validates the event type (push to main branch)
    3. Triggers the deployment script in the background
    
    Security:
    - Requires GITHUB_WEBHOOK_SECRET environment variable
    - Verifies HMAC SHA256 signature
    - Only processes push events to main branch
    
    Usage:
        POST /api/deploy/webhook/
        Headers:
            X-Hub-Signature-256: sha256=<hash>
            X-GitHub-Event: push
        Body: GitHub webhook payload (JSON)
    """
    # Get raw body for signature verification
    payload_body = request.body
    
    # Verify signature
    signature_header = request.headers.get('X-Hub-Signature-256', '')
    if not verify_github_signature(payload_body, signature_header):
        logger.warning(f"Invalid webhook signature from {request.META.get('REMOTE_ADDR')}")
        return HttpResponseForbidden('Invalid signature')
    
    # Parse JSON payload
    try:
        payload = json.loads(payload_body.decode('utf-8'))
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload")
        return JsonResponse({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get event type
    event_type = request.headers.get('X-GitHub-Event', '')
    logger.info(f"Received GitHub webhook event: {event_type}")
    
    # Only process push events
    if event_type != 'push':
        logger.info(f"Ignoring event type: {event_type}")
        return JsonResponse({
            'message': f'Event type {event_type} ignored. Only push events are processed.'
        }, status=status.HTTP_200_OK)
    
    # Check if push is to main branch
    ref = payload.get('ref', '')
    if not ref.endswith('/main') and not ref.endswith('/master'):
        logger.info(f"Ignoring push to branch: {ref}")
        return JsonResponse({
            'message': f'Push to {ref} ignored. Only main/master branch triggers deployment.'
        }, status=status.HTTP_200_OK)
    
    # Get commit information
    commits = payload.get('commits', [])
    if commits:
        latest_commit = commits[-1]
        commit_id = latest_commit.get('id', '')[:7]
        commit_message = latest_commit.get('message', '').split('\n')[0]
        author = latest_commit.get('author', {}).get('name', 'Unknown')
        logger.info(f"Deployment triggered by commit: {commit_id} - {commit_message} ({author})")
    
    # Trigger deployment script in background
    try:
        project_root = Path(settings.BASE_DIR).parent
        deploy_script = project_root / 'auto_deploy.py'
        
        if not deploy_script.exists():
            logger.error(f"Deployment script not found: {deploy_script}")
            return JsonResponse({
                'error': 'Deployment script not found'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Run deployment script in background
        # Use nohup or start detached process depending on platform
        import platform
        if platform.system() == 'Windows':
            # Windows: Use start command
            subprocess.Popen(
                ['python', str(deploy_script)],
                cwd=project_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            # Unix/Linux: Use nohup or run in background
            subprocess.Popen(
                ['python3', str(deploy_script)],
                cwd=project_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        
        logger.info("Deployment script started in background")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Deployment triggered successfully',
            'commit': commit_id if commits else None,
            'branch': ref.split('/')[-1]
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to trigger deployment: {e}", exc_info=True)
        return JsonResponse({
            'error': 'Failed to trigger deployment',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def deployment_status(request):
    """
    Get deployment status from log file.

    Requires ``DEPLOYMENT_STATUS_SECRET`` in Django settings and the same value in
    header ``X-Deployment-Status-Secret`` (timing-safe compare). Disabled when
    the secret is unset to avoid leaking deploy logs publicly.
    """
    configured = getattr(settings, 'DEPLOYMENT_STATUS_SECRET', '') or ''
    if not str(configured).strip():
        logger.warning('deployment_status: DEPLOYMENT_STATUS_SECRET is not set; access denied.')
        return JsonResponse(
            {'detail': 'Deployment status endpoint is not configured.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    provided = request.headers.get('X-Deployment-Status-Secret', '')
    if not secrets.compare_digest(str(configured), str(provided)):
        logger.warning(
            'deployment_status: invalid or missing secret from %s',
            request.META.get('REMOTE_ADDR'),
        )
        return JsonResponse({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        project_root = Path(settings.BASE_DIR).parent
        log_file = project_root / 'deploy_log.txt'
        
        if not log_file.exists():
            return JsonResponse({
                'status': 'no_log',
                'message': 'Deployment log file not found'
            }, status=status.HTTP_200_OK)
        
        # Read last 50 lines
        lines = request.GET.get('lines', 50)
        try:
            lines = int(lines)
        except ValueError:
            lines = 50
        
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return JsonResponse({
            'status': 'success',
            'log': ''.join(last_lines),
            'total_lines': len(all_lines)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to read deployment log: {e}")
        return JsonResponse({
            'error': 'Failed to read deployment log',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

