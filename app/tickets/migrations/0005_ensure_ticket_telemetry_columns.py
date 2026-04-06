"""
Repair migration: ensure client_version and deployment_context exist on tickets_ticket.

Some environments had the model updated before tickets.0003_reports_and_telemetry ran,
or drift between django_migrations and the actual schema. This adds missing columns
idempotently so ORM queries match the database.
"""

from django.db import migrations


def _ticket_table_name(apps):
    Ticket = apps.get_model('tickets', 'Ticket')
    return Ticket._meta.db_table


def _pg_column_exists(cursor, table, column):
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = %s
          AND column_name = %s
        """,
        [table, column],
    )
    return cursor.fetchone() is not None


def _sqlite_column_exists(cursor, table, column):
    cursor.execute(f'PRAGMA table_info({table})')
    return any(row[1] == column for row in cursor.fetchall())


def _mysql_column_exists(cursor, table, column):
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        """,
        [table, column],
    )
    return cursor.fetchone() is not None


def ensure_telemetry_columns(apps, schema_editor):
    table = _ticket_table_name(apps)
    conn = schema_editor.connection
    vendor = conn.vendor

    with conn.cursor() as cursor:
        def exists(col):
            if vendor == 'postgresql':
                return _pg_column_exists(cursor, table, col)
            if vendor == 'sqlite':
                return _sqlite_column_exists(cursor, table, col)
            if vendor == 'mysql':
                return _mysql_column_exists(cursor, table, col)
            return False

        if not exists('client_version'):
            if vendor == 'postgresql':
                cursor.execute(
                    f'ALTER TABLE {conn.ops.quote_name(table)} '
                    f'ADD COLUMN {conn.ops.quote_name("client_version")} '
                    'varchar(64) DEFAULT %s NOT NULL',
                    [''],
                )
            elif vendor == 'sqlite':
                cursor.execute(
                    f'ALTER TABLE {conn.ops.quote_name(table)} '
                    'ADD COLUMN client_version varchar(64) DEFAULT \'\''
                )
            elif vendor == 'mysql':
                cursor.execute(
                    f'ALTER TABLE {conn.ops.quote_name(table)} '
                    'ADD COLUMN client_version varchar(64) NOT NULL DEFAULT \'\''
                )

        if not exists('deployment_context'):
            if vendor == 'postgresql':
                cursor.execute(
                    f'ALTER TABLE {conn.ops.quote_name(table)} '
                    f'ADD COLUMN {conn.ops.quote_name("deployment_context")} '
                    'varchar(32) DEFAULT %s NOT NULL',
                    [''],
                )
            elif vendor == 'sqlite':
                cursor.execute(
                    f'ALTER TABLE {conn.ops.quote_name(table)} '
                    'ADD COLUMN deployment_context varchar(32) DEFAULT \'\''
                )
            elif vendor == 'mysql':
                cursor.execute(
                    f'ALTER TABLE {conn.ops.quote_name(table)} '
                    'ADD COLUMN deployment_context varchar(32) NOT NULL DEFAULT \'\''
                )


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0004_operator_ticket_bridge'),
    ]

    operations = [
        migrations.RunPython(ensure_telemetry_columns, migrations.RunPython.noop),
    ]
