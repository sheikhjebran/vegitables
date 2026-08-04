from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError

from ...repositories.mobile_sales_repository import MobileSalesRepository


class Command(BaseCommand):
    help = 'Write, read, and delete a temporary MobileSalesBill record through the Firestore-backed repository.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--shop-id',
            type=int,
            default=999999,
            help='Temporary shop_id to use for the Firebase smoke test.',
        )

    def handle(self, *args, **options):
        repository = MobileSalesRepository()
        if not repository.using_firebase():
            raise CommandError(
                'Set FIREBASE_ENABLED=True and USE_FIREBASE_MOBILE_SALES=True before running this command.'
            )

        token = uuid4().hex[:12]
        shop_id = options['shop_id']
        customer_name = f'firebase-smoke-{token}'
        lot_no = f'lot-{token}'

        created_record = None
        try:
            created_record = repository.create(
                shop_id=shop_id,
                name=customer_name,
                lot_no=lot_no,
                total_bags=1,
                net_weight=1.25,
            )

            fetched_records = repository.list_by_shop_and_customer_name(shop_id, customer_name)
            if len(fetched_records) != 1:
                raise CommandError(
                    f'Expected 1 Firestore record after create, found {len(fetched_records)}.'
                )

            fetched_record = fetched_records[0]
            if fetched_record.lot_no != lot_no or fetched_record.total_bags != 1:
                raise CommandError('Fetched Firestore record does not match the created payload.')

            deleted_count = repository.delete_by_shop_and_customer_name(shop_id, customer_name)
            if deleted_count != 1:
                raise CommandError(f'Expected to delete 1 Firestore record, deleted {deleted_count}.')

            remaining_records = repository.list_by_shop_and_customer_name(shop_id, customer_name)
            if remaining_records:
                raise CommandError('Temporary Firestore record still exists after delete.')

            self.stdout.write(self.style.SUCCESS('Firebase MobileSalesBill smoke test passed.'))
            self.stdout.write(f'Created temporary record id={created_record.id} for shop_id={shop_id}.')
        except Exception:
            if created_record is not None:
                try:
                    repository.delete_by_shop_and_customer_name(shop_id, customer_name)
                except Exception:
                    pass
            raise