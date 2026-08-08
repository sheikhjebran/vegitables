from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError

from ...repositories.expenditure_repository import ExpenditureRepository


class Command(BaseCommand):
    help = 'Validate Firestore-backed Expenditure repository CRUD and date aggregates.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--shop-id',
            type=int,
            default=None,
            help='Temporary shop_id to use for the Firebase expenditure smoke test. If omitted, a unique ID is generated per run.',
        )

    def handle(self, *args, **options):
        repository = ExpenditureRepository()
        if not repository.using_firebase():
            raise CommandError(
                'Set FIREBASE_ENABLED=True and USE_FIREBASE_EXPENDITURE=True before running this command.'
            )

        token = uuid4().hex[:8]
        shop_id = options['shop_id'] if options['shop_id'] is not None else _generated_shop_id(token)
        today = '2026-08-04'
        created_record = None

        try:
            created_record = repository.create(
                shop_id=shop_id,
                date=today,
                expense_type='CASH',
                amount=12.5,
                remark=f'Expense {token}',
            )

            fetched = repository.get_by_id(created_record.id)
            if fetched is None:
                raise CommandError('Created Firestore expenditure record could not be fetched by id.')
            if round(float(fetched.amount), 2) != 12.5:
                raise CommandError('Created Firestore expenditure amount was not persisted correctly.')

            created_record = repository.update(
                record_id=created_record.id,
                shop_id=shop_id,
                date=today,
                expense_type='UPI',
                amount=15.75,
                remark=f'Expense updated {token}',
            )

            updated = repository.get_by_id(created_record.id)
            if updated is None:
                raise CommandError('Updated Firestore expenditure record could not be fetched by id.')
            if updated.expense_type != 'UPI' or round(float(updated.amount), 2) != 15.75:
                raise CommandError('Firestore expenditure update did not persist expected values.')

            rows = repository.list_by_shop_and_date(shop_id, today)
            if not any(str(item.id) == str(created_record.id) for item in rows):
                raise CommandError('Firestore expenditure list_by_shop_and_date did not include created record.')

            total = repository.sum_amount_by_shop_and_date(shop_id, today)
            if round(float(total), 2) < 15.75:
                raise CommandError('Firestore expenditure sum_amount_by_shop_and_date returned unexpected total.')

            deleted = repository.delete(created_record.id)
            if not deleted:
                raise CommandError('Expected Firestore expenditure record to be deleted.')
            created_record = None

            self.stdout.write(self.style.SUCCESS('Firebase expenditure smoke test passed.'))
            self.stdout.write(f'Validated expenditure Firestore CRUD for shop_id={shop_id}.')

        except KeyboardInterrupt as error:
            if created_record is not None:
                try:
                    repository.delete(created_record.id)
                except Exception:
                    pass
            raise CommandError(
                'Expenditure Firebase smoke test was interrupted while waiting on Firestore. '
                'Retry the command; if the issue persists, check Firestore connectivity and gRPC stability.'
            ) from error

        except Exception:
            if created_record is not None:
                try:
                    repository.delete(created_record.id)
                except Exception:
                    pass
            raise


def _generated_shop_id(token):
    # Keep generated IDs in a high range to avoid clashing with real shops.
    return 900000 + (int(token[:6], 16) % 90000)
