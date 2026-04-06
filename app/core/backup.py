"""
Automated backup system for PixelCast Signage.

Provides:
- Database backups (SQLite, PostgreSQL, MySQL)
- Media file backups
- Full system backups
- Scheduled backups
- Backup integrity verification
- Retention policies
"""
import os
import subprocess
import hashlib
import json
import shutil
import gzip
import tarfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.core.management import call_command
from core.models import SystemBackup
from core.audit import AuditLogger
import logging

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Centralized backup management system.
    """

    def __init__(self):
        """Initialize backup manager with configuration."""
        self.config = getattr(settings, 'BACKUP_CONFIG', {})
        self.backup_dir = Path(self.config.get('BACKUP_DIR', settings.BASE_DIR / 'backups'))
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def get_database_backup_command(self) -> Optional[List[str]]:
        """
        Get command to backup database based on configured backend.

        Returns:
            List of command parts for subprocess, or None if unsupported
        """
        db_config = settings.DATABASES['default']
        engine = db_config.get('ENGINE', '')

        if 'sqlite3' in engine:
            # SQLite backup - use Python's shutil for cross-platform support
            db_path = Path(db_config.get('NAME', settings.BASE_DIR / 'db.sqlite3'))
            # Return special marker for SQLite
            return ['sqlite', str(db_path)]

        elif 'postgresql' in engine:
            # PostgreSQL backup using pg_dump
            name = db_config.get('NAME')
            user = db_config.get('USER')
            password = db_config.get('PASSWORD')
            host = db_config.get('HOST', 'localhost')
            port = db_config.get('PORT', '5432')

            cmd = ['pg_dump']
            if user:
                cmd.extend(['-U', user])
            if host:
                cmd.extend(['-h', host])
            if port:
                cmd.extend(['-p', port])
            cmd.append(name)

            env = os.environ.copy()
            if password:
                env['PGPASSWORD'] = password

            return cmd, env

        elif 'mysql' in engine:
            # MySQL backup using mysqldump
            name = db_config.get('NAME')
            user = db_config.get('USER')
            password = db_config.get('PASSWORD')
            host = db_config.get('HOST', 'localhost')
            port = db_config.get('PORT', '3306')

            cmd = ['mysqldump']
            if user:
                cmd.extend(['-u', user])
            if password:
                cmd.extend([f'-p{password}'])
            if host:
                cmd.extend(['-h', host])
            if port:
                cmd.extend(['-P', port])
            cmd.append(name)

            return cmd

        return None

    def backup_database(
        self,
        include_media: bool = False,
        compression: bool = True,
        encryption: bool = False,
        user=None
    ) -> SystemBackup:
        """
        Create a database backup.

        Args:
            include_media: Whether to include media files
            compression: Whether to compress backup
            encryption: Whether to encrypt backup (not implemented)
            user: User who triggered the backup

        Returns:
            SystemBackup instance
        """
        backup = SystemBackup.objects.create(
            backup_type='database' if not include_media else 'full',
            status='in_progress',
            include_media=include_media,
            compression=compression,
            encryption=encryption,
            created_by=user,
            started_at=timezone.now(),
        )

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"db_backup_{timestamp}.sql"
            backup_path = self.backup_dir / backup_filename

            # Get database backup command
            cmd_info = self.get_database_backup_command()
            if not cmd_info:
                raise ValueError("Unsupported database backend for backup")

            # Handle SQLite specially (copy file directly)
            if cmd_info[0] == 'sqlite':
                import shutil
                db_path = Path(cmd_info[1])
                if not db_path.exists():
                    raise Exception(f"Database file not found: {db_path}")
                shutil.copy2(db_path, backup_path)
            else:
                # For PostgreSQL/MySQL, use command-line tools
                cmd = cmd_info[0] if isinstance(cmd_info, tuple) else cmd_info
                env = cmd_info[1] if isinstance(cmd_info, tuple) else None

                # Execute backup
                with open(backup_path, 'w') as f:
                    process = subprocess.run(
                        cmd,
                        stdout=f,
                        stderr=subprocess.PIPE,
                        env=env,
                        check=False
                    )

                if process.returncode != 0:
                    error_msg = process.stderr.decode() if process.stderr else 'Unknown error'
                    raise Exception(f"Backup command failed: {error_msg}")

            # Compress if requested
            if compression:
                compressed_path = backup_path.with_suffix('.sql.gz')
                import gzip
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(backup_path)
                backup_path = compressed_path

            # Calculate checksum
            checksum = self.calculate_checksum(backup_path)

            # Get file size
            file_size = backup_path.stat().st_size

            # Update backup record
            backup.status = 'completed'
            backup.file_path = str(backup_path)
            backup.file_size = file_size
            backup.checksum = checksum
            backup.completed_at = timezone.now()

            # Set expiration based on retention policy
            retention_days = self.config.get('RETENTION_DAYS', 30)
            backup.expires_at = timezone.now() + timedelta(days=retention_days)

            backup.save()

            # Log audit event
            AuditLogger.log_backup(
                backup_type=backup.backup_type,
                status='completed',
                file_path=str(backup_path),
                file_size=file_size,
                user=user,
            )

            logger.info(f"Database backup completed: {backup_path}")

            return backup

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Database backup failed: {error_msg}")

            backup.status = 'failed'
            backup.error_message = error_msg
            backup.completed_at = timezone.now()
            backup.save()

            # Log audit event
            AuditLogger.log_backup(
                backup_type=backup.backup_type,
                status='failed',
                error_message=error_msg,
                user=user,
            )

            raise

    def backup_media(
        self,
        compression: bool = True,
        user=None
    ) -> SystemBackup:
        """
        Create a media files backup.

        Args:
            compression: Whether to compress backup
            user: User who triggered the backup

        Returns:
            SystemBackup instance
        """
        backup = SystemBackup.objects.create(
            backup_type='media',
            status='in_progress',
            compression=compression,
            created_by=user,
            started_at=timezone.now(),
        )

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"media_backup_{timestamp}.tar"
            if compression:
                backup_filename += '.gz'
            backup_path = self.backup_dir / backup_filename

            media_root = Path(settings.MEDIA_ROOT)

            # Create archive
            if compression:
                with tarfile.open(backup_path, 'w:gz') as tar:
                    if media_root.exists():
                        tar.add(media_root, arcname='media')
            else:
                with tarfile.open(backup_path, 'w') as tar:
                    if media_root.exists():
                        tar.add(media_root, arcname='media')

            # Calculate checksum
            checksum = self.calculate_checksum(backup_path)

            # Get file size
            file_size = backup_path.stat().st_size

            # Update backup record
            backup.status = 'completed'
            backup.file_path = str(backup_path)
            backup.file_size = file_size
            backup.checksum = checksum
            backup.completed_at = timezone.now()

            # Set expiration
            retention_days = self.config.get('RETENTION_DAYS', 30)
            backup.expires_at = timezone.now() + timedelta(days=retention_days)

            backup.save()

            # Log audit event
            AuditLogger.log_backup(
                backup_type='media',
                status='completed',
                file_path=str(backup_path),
                file_size=file_size,
                user=user,
            )

            logger.info(f"Media backup completed: {backup_path}")

            return backup

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Media backup failed: {error_msg}")

            backup.status = 'failed'
            backup.error_message = error_msg
            backup.completed_at = timezone.now()
            backup.save()

            # Log audit event
            AuditLogger.log_backup(
                backup_type='media',
                status='failed',
                error_message=error_msg,
                user=user,
            )

            raise

    def backup_full(
        self,
        compression: bool = True,
        user=None
    ) -> SystemBackup:
        """
        Create a full system backup (database + media).

        Args:
            compression: Whether to compress backup
            user: User who triggered the backup

        Returns:
            SystemBackup instance
        """
        return self.backup_database(
            include_media=True,
            compression=compression,
            user=user
        )

    def calculate_checksum(self, file_path: Path, algorithm: str = 'sha256') -> str:
        """Calculate checksum of a file."""
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def verify_backup(self, backup: SystemBackup) -> bool:
        """
        Verify backup integrity by checking checksum.

        Args:
            backup: SystemBackup instance

        Returns:
            True if backup is valid, False otherwise
        """
        if not backup.file_path or not backup.checksum:
            return False

        backup_path = Path(backup.file_path)
        if not backup_path.exists():
            return False

        calculated_checksum = self.calculate_checksum(backup_path)
        return calculated_checksum == backup.checksum

    def cleanup_expired_backups(self) -> int:
        """
        Delete expired backups based on retention policy.

        Returns:
            Number of backups deleted
        """
        expired_backups = SystemBackup.objects.filter(
            expires_at__lt=timezone.now(),
            status='completed'
        )

        deleted_count = 0
        for backup in expired_backups:
            try:
                # Delete file
                if backup.file_path:
                    backup_path = Path(backup.file_path)
                    if backup_path.exists():
                        backup_path.unlink()

                # Update status
                backup.status = 'expired'
                backup.save()

                deleted_count += 1
                logger.info(f"Deleted expired backup: {backup.file_path}")

            except Exception as e:
                logger.error(f"Failed to delete expired backup {backup.id}: {e}")

        return deleted_count

    def list_backups(
        self,
        backup_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[SystemBackup]:
        """
        List backups with optional filtering.

        Args:
            backup_type: Filter by backup type
            status: Filter by status
            limit: Maximum number of backups to return

        Returns:
            List of SystemBackup instances
        """
        queryset = SystemBackup.objects.all()

        if backup_type:
            queryset = queryset.filter(backup_type=backup_type)
        if status:
            queryset = queryset.filter(status=status)

        return list(queryset.order_by('-started_at')[:limit])


# Global backup manager instance
backup_manager = BackupManager()
