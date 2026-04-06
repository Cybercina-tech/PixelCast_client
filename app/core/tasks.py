"""
Celery tasks for scheduled backups and maintenance.
"""
from celery import shared_task
from core.backup import backup_manager
from core.models import SystemBackup
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task
def run_scheduled_backup(backup_type='database'):
    """
    Celery task to run scheduled backups.

    Args:
        backup_type: Type of backup ('database', 'media', 'full')
    """
    logger.info(f"Starting scheduled {backup_type} backup")

    try:
        if backup_type == 'database':
            backup = backup_manager.backup_database(
                include_media=False,
                compression=True,
                user=None  # System-initiated
            )
        elif backup_type == 'media':
            backup = backup_manager.backup_media(
                compression=True,
                user=None
            )
        elif backup_type == 'full':
            backup = backup_manager.backup_full(
                compression=True,
                user=None
            )
        else:
            logger.error(f"Invalid backup type: {backup_type}")
            return

        # Mark as scheduled
        backup.scheduled = True
        backup.schedule_name = f"auto_{backup_type}"
        backup.save()

        logger.info(f"Scheduled {backup_type} backup completed: {backup.id}")
        return str(backup.id)

    except Exception as e:
        logger.error(f"Scheduled backup failed: {e}")
        raise


@shared_task
def cleanup_expired_backups_task():
    """Celery task to cleanup expired backups."""
    logger.info("Starting cleanup of expired backups")

    try:
        deleted_count = backup_manager.cleanup_expired_backups()
        logger.info(f"Cleaned up {deleted_count} expired backups")
        return deleted_count
    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}")
        raise


@shared_task
def cleanup_old_audit_logs():
    """Archive old audit logs (immutable retention — never hard-deleted by default)."""
    from core.models import AuditLog
    from datetime import timedelta

    logger.info("Starting archive of old audit logs")

    try:
        audit_config = getattr(settings, 'AUDIT_LOGGING', {})
        retention_days = audit_config.get('RETENTION_DAYS', 365)

        cutoff_date = timezone.now() - timedelta(days=retention_days)
        old_logs = AuditLog.objects.filter(timestamp__lt=cutoff_date, is_archived=False)
        count = old_logs.count()

        if count > 0:
            archived_count = old_logs.update(is_archived=True)
            logger.info(f"Archived {archived_count} old audit logs")
            return archived_count
        else:
            logger.info("No old audit logs to archive")
            return 0

    except Exception as e:
        logger.error(f"Audit log archive failed: {e}")
        raise
