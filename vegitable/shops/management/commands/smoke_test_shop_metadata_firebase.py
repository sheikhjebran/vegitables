from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError

from ...repositories.shop_metadata_repository import ShopMetadataRepository


class Command(BaseCommand):
    help = 'Create, update, increment, and delete a temporary Firestore shop metadata document.'

    def handle(self, *args, **options):
        repository = ShopMetadataRepository()
        if not repository.using_firebase():
            raise CommandError(repository.requirement_message())

        token = uuid4().hex[:8]
        owner_user_id = 800000 + (int(token[:6], 16) % 90000)
        shop_id = 900000 + (int(token[2:8], 16) % 90000)
        record = None

        try:
            record = repository.create_or_update(
                owner_user_id=owner_user_id,
                shop_id=shop_id,
                shop_name=f'shop-{token}',
                shop_location='firebase',
                shop_address='temporary smoke test',
                expenditure_entry_prefix='EXP',
                expenditure_entry_counter=1,
                arrival_entry_prefix='ARR',
                arrival_entry_counter=2,
                sales_bill_entry_prefix='SAL',
                sales_bill_entry_counter=3,
                patti_entry_prefix='PAT',
                patti_entry_counter=4,
                customer_ledger_prefix='CUS',
                customer_ledger_counter=5,
                farmer_ledger_prefix='FAR',
                farmer_ledger_counter=6,
                credit_bill_entry_prefix='CRD',
                credit_bill_entry_counter=7,
                shilk_entry_prefix='SHI',
                shilk_entry_counter=8,
                inventory_prefix='INV',
                inventory_counter=9,
            )

            fetched = repository.require_by_owner_user_id(owner_user_id)
            if fetched.shop_id != shop_id:
                raise CommandError('Firestore shop metadata fetch returned the wrong shop id.')

            updated = repository.update_prefixes(
                owner_user_id,
                arrival_entry_prefix='ARRX',
                sales_bill_entry_prefix='SALX',
            )
            if updated.arrival_entry_prefix != 'ARRX' or updated.sales_bill_entry_prefix != 'SALX':
                raise CommandError('Firestore shop metadata prefix update did not persist.')

            incremented = repository.increment_counter(owner_user_id, 'sales_bill_entry_counter')
            if incremented.sales_bill_entry_counter != 4:
                raise CommandError('Firestore shop metadata counter increment did not persist.')

            self.stdout.write(self.style.SUCCESS('Firebase shop metadata smoke test passed.'))
            self.stdout.write(
                f'Created temporary shop metadata id={incremented.id} for owner_user_id={owner_user_id}.'
            )
        finally:
            if record is not None:
                repository.delete(record.id)