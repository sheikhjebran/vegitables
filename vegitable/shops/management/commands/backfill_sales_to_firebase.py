from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError

from vegitable.firebase import describe_firebase_configuration

from ...models import SalesBillEntry, SalesBillItem
from ...repositories.sales_bill_repository import SalesBillRepository


class Command(BaseCommand):
    help = 'Backfill SQL SalesBillEntry and SalesBillItem rows into Firestore for the feature-flagged sales slice.'

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

        repository = SalesBillRepository()
        if not repository.using_firebase():
            raise CommandError(
                'Set USE_FIREBASE_SALES=True and USE_FIREBASE_ARRIVAL=True before running this command so writes target Firestore.'
            )

        queryset = SalesBillEntry.objects.filter(Empty_data=False).order_by('id')
        limit = options['limit']
        if limit and limit > 0:
            queryset = queryset[:limit]

        try:
            rows = list(queryset)
        except OperationalError as exc:
            raise CommandError(self._build_source_db_error(exc)) from exc

        if options['dry_run']:
            self.stdout.write(f'Dry run: {len(rows)} SalesBillEntry rows would be backfilled to Firestore.')
            return

        created = 0
        failures = 0
        for row in rows:
            try:
                items = [
                    {
                        'arrival_entry_id': str(item.arrival_goods.arrival_entry_id),
                        'arrival_goods_local_id': str(item.arrival_goods_id),
                        'item_name': item.item_name,
                        'bags': int(item.bags),
                        'net_weight': item.net_weight,
                        'rates': item.rates,
                        'amount': item.amount,
                    }
                    for item in SalesBillItem.objects.filter(Sales_Bill_Entry=row).order_by('id')
                ]

                repository.import_legacy_record(
                    shop_id=row.shop_id,
                    sales_bill_id=row.sales_bill_id,
                    payment_type=row.payment_type,
                    customer_name=row.customer_name,
                    date=row.date,
                    rmc=row.rmc,
                    commission=row.commission,
                    cooli=row.cooli,
                    total_amount=row.total_amount,
                    paid_amount=row.paid_amount,
                    balance_amount=row.balance_amount,
                    empty_data=row.Empty_data,
                    items=items,
                    created_at_ms=int(row.pk),
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
            raise CommandError('One or more SalesBillEntry rows failed during backfill.')

    def _build_source_db_error(self, exc):
        message = str(exc)
        if 'Unknown server host' in message:
            return (
                'The configured SQL source database is pointing at the PythonAnywhere MySQL host and is not '
                'reachable from this environment. Set USE_CLOUD_DB=False to read from local SQLite, or run the '
                'backfill from the environment that can reach the cloud database.'
            )
        if 'no such table: shops_salesbillentry' in message or 'no such table: shops_salesbillitem' in message:
            return (
                'The local SQLite database does not contain the sales source tables. Either run the SQL migrations '
                'and load the source data locally, or run the backfill from the environment that contains the real '
                'source database.'
            )
        return f'Source database error while reading SalesBillEntry rows: {message}'