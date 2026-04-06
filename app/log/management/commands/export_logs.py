"""
Management command to export logs to CSV or JSON format.

This command allows exporting logs for analysis or backup purposes.

Usage:
    python manage.py export_logs --type screen-status --format csv --output logs.csv
    python manage.py export_logs --type content-download --format json --output logs.json
    python manage.py export_logs --type command-execution --format csv --start-date 2024-01-01
"""

import csv
import json
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
from log.models import ScreenStatusLog, ContentDownloadLog, CommandExecutionLog


class Command(BaseCommand):
    help = 'Export logs to CSV or JSON format'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['screen-status', 'content-download', 'command-execution', 'all'],
            required=True,
            help='Type of logs to export'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['csv', 'json'],
            default='csv',
            help='Export format (default: csv)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (default: logs_<type>_<timestamp>.<ext>)'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date for filtering (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date for filtering (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--screen-id',
            type=str,
            help='Filter by screen ID'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of records to export'
        )

    def handle(self, *args, **options):
        log_type = options['type']
        export_format = options['format']
        output_file = options.get('output')
        start_date = options.get('start_date')
        end_date = options.get('end_date')
        screen_id = options.get('screen_id')
        limit = options.get('limit')
        
        # Parse dates
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            try:
                parsed_start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                raise CommandError(f'Invalid start_date format: {start_date}. Use YYYY-MM-DD.')
        
        if end_date:
            try:
                parsed_end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d')
                parsed_end_date = parsed_end_date + timedelta(days=1)
            except ValueError:
                raise CommandError(f'Invalid end_date format: {end_date}. Use YYYY-MM-DD.')
        
        # Get logs based on type
        if log_type == 'screen-status' or log_type == 'all':
            self._export_screen_status_logs(
                export_format, output_file, parsed_start_date, parsed_end_date, screen_id, limit
            )
        
        if log_type == 'content-download' or log_type == 'all':
            self._export_content_download_logs(
                export_format, output_file, parsed_start_date, parsed_end_date, screen_id, limit
            )
        
        if log_type == 'command-execution' or log_type == 'all':
            self._export_command_execution_logs(
                export_format, output_file, parsed_start_date, parsed_end_date, screen_id, limit
            )
    
    def _export_screen_status_logs(self, format_type, output_file, start_date, end_date, screen_id, limit):
        """Export screen status logs"""
        queryset = ScreenStatusLog.objects.select_related('screen').all()
        
        if screen_id:
            queryset = queryset.filter(screen_id=screen_id)
        if start_date:
            queryset = queryset.filter(recorded_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(recorded_at__lte=end_date)
        if limit:
            queryset = queryset[:limit]
        
        if not output_file:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'screen_status_logs_{timestamp}.{format_type}'
        
        self._export_queryset(queryset, format_type, output_file, [
            'id', 'screen__name', 'status', 'heartbeat_latency',
            'cpu_usage', 'memory_usage', 'recorded_at'
        ])
        
        self.stdout.write(
            self.style.SUCCESS(f'Exported {queryset.count()} screen status logs to {output_file}')
        )
    
    def _export_content_download_logs(self, format_type, output_file, start_date, end_date, screen_id, limit):
        """Export content download logs"""
        queryset = ContentDownloadLog.objects.select_related('content', 'screen').all()
        
        if screen_id:
            queryset = queryset.filter(screen_id=screen_id)
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        if limit:
            queryset = queryset[:limit]
        
        if not output_file:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'content_download_logs_{timestamp}.{format_type}'
        
        self._export_queryset(queryset, format_type, output_file, [
            'id', 'content__name', 'screen__name', 'status', 'retry_count',
            'file_size', 'error_message', 'downloaded_at', 'created_at'
        ])
        
        self.stdout.write(
            self.style.SUCCESS(f'Exported {queryset.count()} content download logs to {output_file}')
        )
    
    def _export_command_execution_logs(self, format_type, output_file, start_date, end_date, screen_id, limit):
        """Export command execution logs"""
        queryset = CommandExecutionLog.objects.select_related('command', 'screen').all()
        
        if screen_id:
            queryset = queryset.filter(screen_id=screen_id)
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        if limit:
            queryset = queryset[:limit]
        
        if not output_file:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'command_execution_logs_{timestamp}.{format_type}'
        
        self._export_queryset(queryset, format_type, output_file, [
            'id', 'command__name', 'command__type', 'screen__name', 'status',
            'started_at', 'finished_at', 'error_message', 'created_at'
        ])
        
        self.stdout.write(
            self.style.SUCCESS(f'Exported {queryset.count()} command execution logs to {output_file}')
        )
    
    def _export_queryset(self, queryset, format_type, output_file, fields):
        """Export queryset to CSV or JSON"""
        if format_type == 'csv':
            self._export_to_csv(queryset, output_file, fields)
        else:
            self._export_to_json(queryset, output_file, fields)
    
    def _export_to_csv(self, queryset, output_file, fields):
        """Export queryset to CSV"""
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(fields)
            
            # Write data
            for obj in queryset:
                row = []
                for field in fields:
                    value = self._get_field_value(obj, field)
                    row.append(value)
                writer.writerow(row)
    
    def _export_to_json(self, queryset, output_file, fields):
        """Export queryset to JSON"""
        data = []
        for obj in queryset:
            record = {}
            for field in fields:
                value = self._get_field_value(obj, field)
                # Convert datetime to ISO format
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                record[field] = value
            data.append(record)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _get_field_value(self, obj, field):
        """Get field value, handling related fields"""
        if '__' in field:
            parts = field.split('__')
            value = obj
            for part in parts:
                value = getattr(value, part, None)
                if value is None:
                    return None
            return value
        return getattr(obj, field, None)
