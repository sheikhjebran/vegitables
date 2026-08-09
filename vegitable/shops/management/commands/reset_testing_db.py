from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections


class Command(BaseCommand):
    help = 'Reset the local SQLite database for testing only, then re-run migrations.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Confirm that you want to reset the database.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would happen without deleting the database.',
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Database reset is blocked because DEBUG is False.')

        db_engine = settings.DATABASES['default']['ENGINE']
        if not db_engine.endswith('sqlite3'):
            raise CommandError('Database reset command supports only local SQLite databases.')

        db_name = settings.DATABASES['default']['NAME']
        db_path = Path(db_name)

        if not options['yes']:
            raise CommandError('Pass --yes to confirm database reset.')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING(f'DRY RUN: would reset SQLite DB at {db_path}'))
            return

        for connection in connections.all():
            connection.close()

        if db_path.exists():
            db_path.unlink()
            self.stdout.write(self.style.WARNING(f'Deleted SQLite DB: {db_path}'))
        else:
            self.stdout.write(self.style.WARNING(f'SQLite DB not found, creating new one: {db_path}'))

        call_command('migrate', interactive=False)
        self.stdout.write(self.style.SUCCESS('Database reset complete. Migrations were re-applied.'))
