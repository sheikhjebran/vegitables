from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError

from ...repositories.customer_ledger_repository import CustomerLedgerRepository


class Command(BaseCommand):
    help = 'Write, read, search, update, and delete a temporary CustomerLedger record through the Firestore-backed repository.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--shop-id',
            type=int,
            default=999999,
            help='Temporary shop_id to use for the Firebase smoke test.',
        )

    def handle(self, *args, **options):
        repository = CustomerLedgerRepository()
        if not repository.using_firebase():
            raise CommandError(
                'Set FIREBASE_ENABLED=True and USE_FIREBASE_CUSTOMER_LEDGER=True before running this command.'
            )

        token = uuid4().hex[:12]
        shop_id = options['shop_id']
        created_record = None
        initial_name = f'firebase-customer-{token}'
        contact = f'90000{token[:5]}'
        initial_address = f'{token} market lane'

        try:
            created_record = repository.create(
                shop_id=shop_id,
                name=initial_name,
                contact=contact,
                address=initial_address,
            )

            fetched_record = repository.get_by_id(created_record.id)
            if fetched_record is None or fetched_record.contact != contact:
                raise CommandError('Created Firestore customer record could not be fetched correctly.')

            search_results = repository.search(shop_id=shop_id, search_text=token[:6])
            if not any(str(record.id) == str(created_record.id) for record in search_results):
                raise CommandError('Created Firestore customer record was not found via repository search.')

            updated_name = initial_name + '-updated'
            updated_address = initial_address + ' updated'
            repository.update(
                record_id=created_record.id,
                shop_id=shop_id,
                name=updated_name,
                contact=contact,
                address=updated_address,
            )

            updated_record = repository.get_by_id(created_record.id)
            if updated_record is None or updated_record.name != updated_name:
                raise CommandError('Updated Firestore customer record does not reflect the new values.')

            deleted = repository.delete(created_record.id)
            if not deleted:
                raise CommandError('Expected the temporary Firestore customer record to be deleted.')

            if repository.get_by_id(created_record.id) is not None:
                raise CommandError('Temporary Firestore customer record still exists after delete.')

            self.stdout.write(self.style.SUCCESS('Firebase CustomerLedger smoke test passed.'))
            self.stdout.write(f'Created temporary record id={created_record.id} for shop_id={shop_id}.')
        except Exception:
            if created_record is not None:
                try:
                    repository.delete(created_record.id)
                except Exception:
                    pass
            raise