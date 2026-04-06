"""
Management command to verify database connection.

Usage:
    python manage.py db_check
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import sys


class Command(BaseCommand):
    help = 'Verify database connection and display connection info'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Display detailed connection information',
        )

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        
        # Get database configuration
        db_config = settings.DATABASES['default']
        engine = db_config.get('ENGINE', '')
        db_name = db_config.get('NAME', '')
        db_user = db_config.get('USER', '')
        db_host = db_config.get('HOST', '')
        db_port = db_config.get('PORT', '')
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Database Connection Check'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Display database info
        self.stdout.write(f"Engine: {engine}")
        self.stdout.write(f"Database: {db_name}")
        self.stdout.write(f"User: {db_user}")
        self.stdout.write(f"Host: {db_host}")
        self.stdout.write(f"Port: {db_port}")
        
        if verbose:
            self.stdout.write(f"\nFull Configuration:")
            for key, value in db_config.items():
                if key == 'PASSWORD':
                    self.stdout.write(f"  {key}: {'*' * len(str(value)) if value else 'Not set'}")
                else:
                    self.stdout.write(f"  {key}: {value}")
        
        self.stdout.write("\n" + "-" * 60)
        self.stdout.write("Testing connection...")
        
        try:
            # Test connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
            if result:
                self.stdout.write(self.style.SUCCESS('✓ Connection successful!'))
                
                # Get PostgreSQL version if using PostgreSQL
                if 'postgresql' in engine.lower():
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("SELECT version();")
                            version = cursor.fetchone()[0]
                            self.stdout.write(self.style.SUCCESS(f'✓ PostgreSQL Version: {version}'))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'Could not get PostgreSQL version: {e}'))
                
                # Test query
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port();")
                        db_info = cursor.fetchone()
                        if db_info:
                            self.stdout.write(self.style.SUCCESS(f'✓ Current Database: {db_info[0]}'))
                            self.stdout.write(self.style.SUCCESS(f'✓ Current User: {db_info[1]}'))
                            if verbose and db_info[2]:
                                self.stdout.write(self.style.SUCCESS(f'✓ Server Address: {db_info[2]}:{db_info[3]}'))
                except Exception as e:
                    # This query might fail for non-PostgreSQL databases
                    pass
                
                self.stdout.write(self.style.SUCCESS('\n✓ Database connection is working correctly!'))
                self.stdout.write(self.style.SUCCESS('=' * 60))
                return 0
                
        except Exception as e:
            self.stdout.write(self.style.ERROR('✗ Connection failed!'))
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            self.stdout.write("\nTroubleshooting tips:")
            self.stdout.write("  1. Ensure PostgreSQL container is running: docker-compose ps")
            self.stdout.write("  2. Check database credentials in .env file")
            self.stdout.write("  3. Verify DB_HOST and DB_PORT are correct")
            self.stdout.write("  4. Check if database exists: docker-compose exec db psql -U pixelcast_signage_user -l")
            self.stdout.write(self.style.ERROR('=' * 60))
            sys.exit(1)

