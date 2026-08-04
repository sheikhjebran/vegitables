from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError

from vegitable.firebase import describe_firebase_configuration

from ...models import PattiEntry, PattiEntryList
from ...repositories.patti_repository import PattiRepository


class Command(BaseCommand):
    help = 'Backfill SQL PattiEntry and PattiEntryList rows into Firestore for the feature-flagged patti slice.'

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

        repository = PattiRepository()
        if not repository.using_firebase():
            raise CommandError(
                'Set USE_FIREBASE_PATTI=True before running this command so writes target Firestore.'
            )

        queryset = PattiEntry.objects.order_by('id')
        limit = options['limit']
        if limit and limit > 0:
            queryset = queryset[:limit]

        try:
            rows = list(queryset)
        except OperationalError as exc:
            raise CommandError(self._build_source_db_error(exc)) from exc

        if options['dry_run']:
            self.stdout.write(f'Dry run: {len(rows)} PattiEntry rows would be backfilled to Firestore.')
            return

        created = 0
        failures = 0
        for row in rows:
            try:
                items = [
                    {
                        'item': item.item,
                        'lot_no': item.lot_no,
                        'weight': item.weight,
                        'rate': item.rate,
                        'amount': float(item.amount),
                    }
                    for item in PattiEntryList.objects.filter(patti=row)
                ]
                repository.create(
                    shop_id=row.shop_id,
                    patti_id=row.patti_id,
                    lorry_no=row.lorry_no,
                    date=row.date,
                    advance=row.advance,
                    farmer_name=row.farmer_name,
                    total_weight=row.total_weight,
                    hamali=row.hamali,
                    net_amount=row.net_amount,
                    items=items,
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
            raise CommandError('One or more PattiEntry rows failed during backfill.')

    def _build_source_db_error(self, exc):
        message = str(exc)
        if 'Unknown server host' in message:
            return (
                'The configured SQL source database is pointing at the PythonAnywhere MySQL host and is not '
                'reachable from this environment. Set USE_CLOUD_DB=False to read from local SQLite, or run the '
                'backfill from the environment that can reach the cloud database.'
            )
        if 'no such table: shops_pattientry' in message or 'no such table: shops_pattientrylist' in message:
            return (
                'The local SQLite database does not contain the patti source tables. Either run the SQL migrations '
                'and load the source data locally, or run the backfill from the environment that contains the real '
                'source database.'
            )
        return f'Source database error while reading PattiEntry rows: {message}'
