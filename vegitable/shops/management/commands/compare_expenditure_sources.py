from collections import Counter

from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError

from vegitable.firebase import describe_firebase_configuration, initialize_project_firebase

from ...firebase_models.expenditure import ExpenditureEntryDocument
from ...models import ExpenditureEntry


def build_sql_signature(row):
    return (
        int(row.shop_id),
        str(row.date),
        str(row.expense_type),
        round(float(row.amount), 4),
        str(row.remark),
        bool(row.Empty_data),
    )


def build_firebase_signature(row):
    return (
        int(row.shop_id),
        str(row.date),
        str(row.expense_type),
        round(float(row.amount), 4),
        str(row.remark),
        bool(row.empty_data),
    )


class Command(BaseCommand):
    help = 'Compare SQL ExpenditureEntry rows against Firestore ExpenditureEntry documents.'

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
            sql_rows = list(ExpenditureEntry.objects.order_by('id'))
        except OperationalError as exc:
            raise CommandError(self._build_source_db_error(exc)) from exc
        firebase_rows = list(ExpenditureEntryDocument.objects.all())

        sql_counter = Counter(build_sql_signature(row) for row in sql_rows)
        firebase_counter = Counter(build_firebase_signature(row) for row in firebase_rows)

        sql_only = sql_counter - firebase_counter
        firebase_only = firebase_counter - sql_counter

        self.stdout.write(f'SQL rows: {len(sql_rows)}')
        self.stdout.write(f'Firestore rows: {len(firebase_rows)}')

        mismatch_limit = max(options['show_mismatches'], 0)
        if sql_only or firebase_only:
            self.stdout.write(self.style.WARNING('Expenditure source mismatch detected.'))
            if mismatch_limit:
                self._print_counter('Present only in SQL', sql_only, mismatch_limit)
                self._print_counter('Present only in Firestore', firebase_only, mismatch_limit)
            raise CommandError('SQL and Firestore Expenditure records are not in parity.')

        self.stdout.write(self.style.SUCCESS('SQL and Firestore Expenditure records are in parity.'))

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
        if 'no such table: shops_expenditureentry' in message:
            return (
                'The local SQLite database does not contain the expenditure source table. Either run the SQL '
                'migrations and load the source data locally, or run the parity check from the environment that '
                'contains the real source database.'
            )
        return f'Source database error while reading ExpenditureEntry rows: {message}'
