from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError

from vegitable.firebase import describe_firebase_configuration

from ...models import CreditBillEntry, CreditBillHistory
from ...repositories.credit_bill_repository import CreditBillRepository
from ...repositories.sales_bill_repository import SalesBillRepository


class Command(BaseCommand):
    help = 'Backfill SQL CreditBillEntry and CreditBillHistory rows into Firestore for the feature-flagged credit slice.'

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

        credit_repository = CreditBillRepository()
        sales_repository = SalesBillRepository()
        if not credit_repository.using_firebase():
            raise CommandError(
                'Set USE_FIREBASE_SALES=True and USE_FIREBASE_CREDIT=True before running this command so writes target Firestore.'
            )

        queryset = CreditBillEntry.objects.order_by('id')
        limit = options['limit']
        if limit and limit > 0:
            queryset = queryset[:limit]

        try:
            rows = list(queryset)
        except OperationalError as exc:
            raise CommandError(self._build_source_db_error(exc)) from exc

        if options['dry_run']:
            self.stdout.write(f'Dry run: {len(rows)} CreditBillEntry rows would be backfilled to Firestore.')
            return

        created = 0
        failures = 0
        for row in rows:
            try:
                sales_record = sales_repository.get_by_sales_bill_id(row.shop_id, row.sales_bill.sales_bill_id)
                if sales_record is None:
                    raise ValueError(
                        f'Firestore sales record was not found for SQL sales_bill_id={row.sales_bill.sales_bill_id}. '
                        'Backfill sales before backfilling credit.'
                    )

                histories = [
                    {
                        'date': history.date,
                        'amount': history.amount,
                        'payment_mode': history.payment_mode,
                    }
                    for history in CreditBillHistory.objects.filter(credit_bill=row).order_by('id')
                ]

                credit_repository.import_legacy_record(
                    shop_id=row.shop_id,
                    customer_name=row.customer_name,
                    sales_bill_record_id=sales_record.id,
                    sales_bill_id=row.sales_bill.sales_bill_id,
                    initial_credit_bill_amount=row.initial_credit_bill_amount,
                    histories=histories,
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
            raise CommandError('One or more CreditBillEntry rows failed during backfill.')

    def _build_source_db_error(self, exc):
        message = str(exc)
        if 'Unknown server host' in message:
            return (
                'The configured SQL source database is pointing at the PythonAnywhere MySQL host and is not '
                'reachable from this environment. Set USE_CLOUD_DB=False to read from local SQLite, or run the '
                'backfill from the environment that can reach the cloud database.'
            )
        if 'no such table: shops_creditbillentry' in message or 'no such table: shops_creditbillhistory' in message:
            return (
                'The local SQLite database does not contain the credit source tables. Either run the SQL migrations '
                'and load the source data locally, or run the backfill from the environment that contains the real '
                'source database.'
            )
        return f'Source database error while reading CreditBillEntry rows: {message}'