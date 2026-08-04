from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError

from vegitable.firebase import describe_firebase_configuration

from ...models import ArrivalEntry, ArrivalGoods
from ...repositories.arrival_repository import ArrivalRepository


class Command(BaseCommand):
    help = 'Backfill SQL ArrivalEntry and ArrivalGoods rows into Firestore for the feature-flagged arrival slice.'

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

        repository = ArrivalRepository()
        if not repository.using_firebase():
            raise CommandError(
                'Set USE_FIREBASE_ARRIVAL=True before running this command so writes target Firestore.'
            )

        queryset = ArrivalEntry.objects.filter(Empty_data=False).order_by('id')
        limit = options['limit']
        if limit and limit > 0:
            queryset = queryset[:limit]

        try:
            rows = list(queryset)
        except OperationalError as exc:
            raise CommandError(self._build_source_db_error(exc)) from exc

        if options['dry_run']:
            self.stdout.write(f'Dry run: {len(rows)} ArrivalEntry rows would be backfilled to Firestore.')
            return

        created = 0
        failures = 0
        for row in rows:
            try:
                goods_rows = ArrivalGoods.objects.filter(arrival_entry=row).order_by('id')
                goods = [
                    {
                        'local_id': str(item.pk),
                        'former_name': item.former_name,
                        'item_name': item.item_name,
                        'initial_qty': item.initial_qty,
                        'qty': item.qty,
                        'weight': item.weight,
                        'remarks': item.remarks,
                        'advance': item.advance,
                        'patti_status': item.patti_status,
                    }
                    for item in goods_rows
                ]

                repository.create(
                    shop_id=row.shop_id,
                    arrival_id=row.arrival_id,
                    gp_no=row.gp_no,
                    lorry_no=row.lorry_no,
                    date=row.date,
                    patti_name=row.patti_name,
                    total_bags=row.total_bags,
                    empty_data=row.Empty_data,
                    goods=goods,
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
            raise CommandError('One or more ArrivalEntry rows failed during backfill.')

    def _build_source_db_error(self, exc):
        message = str(exc)
        if 'Unknown server host' in message:
            return (
                'The configured SQL source database is pointing at the PythonAnywhere MySQL host and is not '
                'reachable from this environment. Set USE_CLOUD_DB=False to read from local SQLite, or run the '
                'backfill from the environment that can reach the cloud database.'
            )
        if 'no such table: shops_arrivalentry' in message or 'no such table: shops_arrivalgoods' in message:
            return (
                'The local SQLite database does not contain the arrival source tables. Either run the SQL migrations '
                'and load the source data locally, or run the backfill from the environment that contains the real '
                'source database.'
            )
        return f'Source database error while reading ArrivalEntry rows: {message}'
