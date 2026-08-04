from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError

from ...repositories.farmer_ledger_repository import FarmerLedgerRepository


class Command(BaseCommand):
    help = 'Write, read, search, update, and delete a temporary FarmerLedger record through the Firestore-backed repository.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--shop-id',
            type=int,
            default=999999,
            help='Temporary shop_id to use for the Firebase smoke test.',
        )

    def handle(self, *args, **options):
        repository = FarmerLedgerRepository()
        if not repository.using_firebase():
            raise CommandError(
                'Set FIREBASE_ENABLED=True and USE_FIREBASE_FARMER_LEDGER=True before running this command.'
            )

        token = uuid4().hex[:12]
        shop_id = options['shop_id']
        created_record = None
        initial_name = f'firebase-farmer-{token}'
        contact = f'81111{token[:5]}'
        initial_place = f'{token} village'

        try:
            created_record = repository.create(
                shop_id=shop_id,
                name=initial_name,
                contact=contact,
                place=initial_place,
            )

            fetched_record = repository.get_by_id(created_record.id)
            if fetched_record is None or fetched_record.contact != contact:
                raise CommandError('Created Firestore farmer record could not be fetched correctly.')

            search_results = repository.search(shop_id=shop_id, search_text=token[:6])
            if not any(str(record.id) == str(created_record.id) for record in search_results):
                raise CommandError('Created Firestore farmer record was not found via repository search.')

            updated_name = initial_name + '-updated'
            updated_place = initial_place + ' updated'
            repository.update(
                record_id=created_record.id,
                shop_id=shop_id,
                name=updated_name,
                contact=contact,
                place=updated_place,
            )

            updated_record = repository.get_by_id(created_record.id)
            if updated_record is None or updated_record.name != updated_name:
                raise CommandError('Updated Firestore farmer record does not reflect the new values.')

            deleted = repository.delete(created_record.id)
            if not deleted:
                raise CommandError('Expected the temporary Firestore farmer record to be deleted.')

            if repository.get_by_id(created_record.id) is not None:
                raise CommandError('Temporary Firestore farmer record still exists after delete.')

            self.stdout.write(self.style.SUCCESS('Firebase FarmerLedger smoke test passed.'))
            self.stdout.write(f'Created temporary record id={created_record.id} for shop_id={shop_id}.')
        except Exception:
            if created_record is not None:
                try:
                    repository.delete(created_record.id)
                except Exception:
                    pass
            raise