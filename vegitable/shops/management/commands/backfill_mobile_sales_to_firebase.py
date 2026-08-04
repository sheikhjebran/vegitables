from django.db import OperationalError
from django.core.management.base import BaseCommand, CommandError

from vegitable.firebase import describe_firebase_configuration

from ...models import MobileSalesBill
from ...repositories.mobile_sales_repository import MobileSalesRepository


class Command(BaseCommand):
    help = 'Backfill SQL MobileSalesBill rows into Firestore for the feature-flagged mobile sales slice.'

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

        repository = MobileSalesRepository()
        if not repository.using_firebase():
            raise CommandError(
                'Set USE_FIREBASE_MOBILE_SALES=True before running this command so writes target Firestore.'
            )

        queryset = MobileSalesBill.objects.order_by('id')
        limit = options['limit']
        if limit and limit > 0:
            queryset = queryset[:limit]

        try:
            rows = list(queryset)
        except OperationalError as exc:
            raise CommandError(self._build_source_db_error(exc)) from exc

        if options['dry_run']:
            self.stdout.write(f'Dry run: {len(rows)} MobileSalesBill rows would be backfilled to Firestore.')
            return

        created = 0
        failures = 0
        for row in rows:
            try:
                repository.create(
                    shop_id=row.shop.pk,
                    name=row.name,
                    lot_no=row.lot_no,
                    total_bags=row.total_bags,
                    net_weight=row.net_weight,
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
            raise CommandError('One or more MobileSalesBill rows failed during backfill.')

    def _build_source_db_error(self, exc):
        message = str(exc)
        if 'Unknown server host' in message:
            return (
                'The configured SQL source database is pointing at the PythonAnywhere MySQL host and is not '
                'reachable from this environment. Set USE_CLOUD_DB=False to read from local SQLite, or run the '
                'backfill from the environment that can reach the cloud database.'
            )
        if 'no such table: shops_mobilesalesbill' in message:
            return (
                'The local SQLite database does not contain the shops_mobilesalesbill table. Either run the '
                'SQL migrations and load the source data locally, or run the backfill from the environment that '
                'contains the real source database.'
            )
        return f'Source database error while reading MobileSalesBill rows: {message}'