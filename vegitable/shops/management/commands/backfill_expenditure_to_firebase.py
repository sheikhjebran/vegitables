from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError

from vegitable.firebase import describe_firebase_configuration

from ...models import ExpenditureEntry
from ...repositories.expenditure_repository import ExpenditureRepository


class Command(BaseCommand):
    help = 'Backfill SQL ExpenditureEntry rows into Firestore for the feature-flagged expenditure slice.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report how many rows would be copied without writing to Firestore.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Optional maximum number of rows to backfill.',
        )

    def handle(self, *args, **options):
        configuration = describe_firebase_configuration()
        if not configuration['enabled']:
            raise CommandError('Set FIREBASE_ENABLED=True before running this command.')

        repository = ExpenditureRepository()
        if not repository.using_firebase():
            raise CommandError(
                'Set USE_FIREBASE_EXPENDITURE=True before running this command so writes target Firestore.'
            )

        queryset = ExpenditureEntry.objects.order_by('id')
        limit = options['limit']
        if limit and limit > 0:
            queryset = queryset[:limit]

        try:
            rows = list(queryset)
        except OperationalError as exc:
            raise CommandError(self._build_source_db_error(exc)) from exc

        if options['dry_run']:
            self.stdout.write(f'Dry run: {len(rows)} ExpenditureEntry rows would be backfilled to Firestore.')
            return

        created = 0
        failures = 0
        for row in rows:
            try:
                repository.create(
                    shop_id=row.shop_id,
                    date=row.date,
                    expense_type=row.expense_type,
                    amount=row.amount,
                    remark=row.remark,
                    empty_data=row.Empty_data,
                )
                created += 1
            except Exception as exc:
                failures += 1
                self.stderr.write(f'Failed row id={row.pk}: {exc}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Backfill finished. created={created} failures={failures} source_rows={len(rows)}'
            )
        )
        if failures:
            raise CommandError('One or more ExpenditureEntry rows failed during backfill.')

    def _build_source_db_error(self, exc):
        message = str(exc)
        if 'Unknown server host' in message:
            return (
                'The configured SQL source database is pointing at the PythonAnywhere MySQL host and is not '
                'reachable from this environment. Set USE_CLOUD_DB=False to read from local SQLite, or run the '
                'backfill from the environment that can reach the cloud database.'
            )
        if 'no such table: shops_expenditureentry' in message:
            return (
                'The local SQLite database does not contain the expenditure source table. Either run the SQL '
                'migrations and load the source data locally, or run the backfill from the environment that '
                'contains the real source database.'
            )
        return f'Source database error while reading ExpenditureEntry rows: {message}'
