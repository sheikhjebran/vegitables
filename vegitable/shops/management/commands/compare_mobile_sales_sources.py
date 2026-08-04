from collections import Counter

from django.db import OperationalError
from django.core.management.base import BaseCommand, CommandError

from vegitable.firebase import describe_firebase_configuration, initialize_project_firebase

from ...firebase_models.mobile_sales import MobileSalesBillDocument
from ...models import MobileSalesBill


def build_signature(*, shop_id, name, lot_no, total_bags, net_weight):
    return (
        int(shop_id),
        str(name),
        str(lot_no),
        int(total_bags),
        round(float(net_weight), 4),
    )


class Command(BaseCommand):
    help = 'Compare SQL MobileSalesBill rows against Firestore MobileSalesBill documents.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--show-mismatches',
            type=int,
            default=10,
            help='Maximum number of mismatched signatures to print for each side.',
        )

    def handle(self, *args, **options):
        configuration = describe_firebase_configuration()
        if not configuration['enabled']:
            raise CommandError('Set FIREBASE_ENABLED=True before running this command.')

        initialize_project_firebase()

        try:
            sql_rows = list(MobileSalesBill.objects.order_by('id'))
        except OperationalError as exc:
            raise CommandError(self._build_source_db_error(exc)) from exc
        firebase_rows = list(MobileSalesBillDocument.objects.all())

        sql_counter = Counter(
            build_signature(
                shop_id=row.shop_id,
                name=row.name,
                lot_no=row.lot_no,
                total_bags=row.total_bags,
                net_weight=row.net_weight,
            )
            for row in sql_rows
        )
        firebase_counter = Counter(
            build_signature(
                shop_id=row.shop_id,
                name=row.name,
                lot_no=row.lot_no,
                total_bags=row.total_bags,
                net_weight=row.net_weight,
            )
            for row in firebase_rows
        )

        sql_only = sql_counter - firebase_counter
        firebase_only = firebase_counter - sql_counter

        self.stdout.write(f'SQL rows: {len(sql_rows)}')
        self.stdout.write(f'Firestore rows: {len(firebase_rows)}')

        mismatch_limit = max(options['show_mismatches'], 0)
        if sql_only or firebase_only:
            self.stdout.write(self.style.WARNING('MobileSalesBill source mismatch detected.'))
            if mismatch_limit:
                self._print_counter('Present only in SQL', sql_only, mismatch_limit)
                self._print_counter('Present only in Firestore', firebase_only, mismatch_limit)
            raise CommandError('SQL and Firestore MobileSalesBill records are not in parity.')

        self.stdout.write(self.style.SUCCESS('SQL and Firestore MobileSalesBill records are in parity.'))

    def _print_counter(self, title, counter, limit):
        self.stdout.write(title + ':')
        for index, (signature, count) in enumerate(counter.items()):
            if index >= limit:
                remaining = len(counter) - limit
                if remaining > 0:
                    self.stdout.write(f'  ... {remaining} more mismatches not shown')
                break
            self.stdout.write(f'  count={count} signature={signature}')

    def _build_source_db_error(self, exc):
        message = str(exc)
        if 'Unknown server host' in message:
            return (
                'The configured SQL source database is pointing at the PythonAnywhere MySQL host and is not '
                'reachable from this environment. Set USE_CLOUD_DB=False to read from local SQLite, or run the '
                'parity check from the environment that can reach the cloud database.'
            )
        if 'no such table: shops_mobilesalesbill' in message:
            return (
                'The local SQLite database does not contain the shops_mobilesalesbill table. Either run the '
                'SQL migrations and load the source data locally, or run the parity check from the environment '
                'that contains the real source database.'
            )
        return f'Source database error while reading MobileSalesBill rows: {message}'