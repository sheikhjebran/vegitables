from collections import Counter

from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError

from vegitable.firebase import describe_firebase_configuration, initialize_project_firebase

from ...firebase_models.arrival import ArrivalEntryDocument
from ...models import ArrivalEntry, ArrivalGoods


def _normalize_goods(items):
    normalized = []
    for item in items:
        normalized.append(
            (
                str(item.get('local_id', '')),
                str(item.get('former_name', '')),
                str(item.get('item_name', '')),
                int(item.get('initial_qty', 0)),
                int(item.get('qty', 0)),
                round(float(item.get('weight', 0.0)), 4),
                str(item.get('remarks', '')),
                round(float(item.get('advance', 0.0)), 4),
                bool(item.get('patti_status', False)),
            )
        )
    return tuple(sorted(normalized))


def _normalize_sql_goods(entry):
    rows = ArrivalGoods.objects.filter(arrival_entry=entry).order_by('id')
    return tuple(
        sorted(
            (
                str(row.pk),
                str(row.former_name),
                str(row.item_name),
                int(row.initial_qty),
                int(row.qty),
                round(float(row.weight), 4),
                str(row.remarks),
                round(float(row.advance), 4),
                bool(row.patti_status),
            )
            for row in rows
        )
    )


def build_sql_signature(row):
    return (
        int(row.shop_id),
        str(row.arrival_id),
        str(row.gp_no),
        str(row.lorry_no),
        str(row.date),
        str(row.patti_name),
        int(row.total_bags),
        bool(row.Empty_data),
        _normalize_sql_goods(row),
    )


def build_firebase_signature(row):
    return (
        int(row.shop_id),
        str(row.arrival_id),
        str(row.gp_no),
        str(row.lorry_no),
        str(row.date),
        str(row.patti_name),
        int(row.total_bags),
        bool(row.empty_data),
        _normalize_goods(list(row.goods or [])),
    )


class Command(BaseCommand):
    help = 'Compare SQL ArrivalEntry rows against Firestore ArrivalEntry documents.'

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
            sql_rows = list(ArrivalEntry.objects.filter(Empty_data=False).order_by('id'))
        except OperationalError as exc:
            raise CommandError(self._build_source_db_error(exc)) from exc
        firebase_rows = list(ArrivalEntryDocument.objects.all())

        sql_counter = Counter(build_sql_signature(row) for row in sql_rows)
        firebase_counter = Counter(build_firebase_signature(row) for row in firebase_rows)

        sql_only = sql_counter - firebase_counter
        firebase_only = firebase_counter - sql_counter

        self.stdout.write(f'SQL rows: {len(sql_rows)}')
        self.stdout.write(f'Firestore rows: {len(firebase_rows)}')

        mismatch_limit = max(options['show_mismatches'], 0)
        if sql_only or firebase_only:
            self.stdout.write(self.style.WARNING('Arrival source mismatch detected.'))
            if mismatch_limit:
                self._print_counter('Present only in SQL', sql_only, mismatch_limit)
                self._print_counter('Present only in Firestore', firebase_only, mismatch_limit)
            raise CommandError('SQL and Firestore Arrival records are not in parity.')

        self.stdout.write(self.style.SUCCESS('SQL and Firestore Arrival records are in parity.'))

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
        if 'no such table: shops_arrivalentry' in message or 'no such table: shops_arrivalgoods' in message:
            return (
                'The local SQLite database does not contain the arrival source tables. Either run the SQL migrations '
                'and load the source data locally, or run the parity check from the environment that contains the '
                'real source database.'
            )
        return f'Source database error while reading ArrivalEntry rows: {message}'
