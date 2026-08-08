from django.db import OperationalError
from django.core.management.base import BaseCommand, CommandError

from ...models import Index, Shop
from ...repositories.shop_metadata_repository import ShopMetadataRepository


class Command(BaseCommand):
    help = 'Backfill Shop and Index metadata to Firestore for Firebase-only runtime lookups.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be written without persisting metadata to Firestore.',
        )

    def handle(self, *args, **options):
        repository = ShopMetadataRepository()
        if not repository.using_firebase():
            raise CommandError(repository.requirement_message())

        dry_run = options['dry_run']
        rows_written = 0

        try:
            for shop in Shop.objects.all().order_by('id'):
                index = Index.objects.filter(shop=shop).first()
                if index is None:
                    self.stdout.write(self.style.WARNING(f'Skipping shop {shop.pk}: no Index row found.'))
                    continue

                rows_written += 1
                if dry_run:
                    self.stdout.write(
                        f'DRY RUN shop_id={shop.pk} owner_user_id={shop.shop_owner_id} '
                        f'arrival_prefix={index.arrival_entry_prefix} sales_prefix={index.sales_bill_entry_prefix}'
                    )
                    continue

                repository.create_or_update(
                    owner_user_id=shop.shop_owner_id,
                    shop_id=shop.pk,
                    shop_name=shop.shop_name,
                    shop_location=shop.shop_location,
                    shop_address=shop.shop_address,
                    expenditure_entry_prefix=index.expenditure_entry_prefix,
                    expenditure_entry_counter=index.expenditure_entry_counter,
                    arrival_entry_prefix=index.arrival_entry_prefix,
                    arrival_entry_counter=index.arrival_entry_counter,
                    sales_bill_entry_prefix=index.sales_bill_entry_prefix,
                    sales_bill_entry_counter=index.sales_bill_entry_counter,
                    patti_entry_prefix=index.patti_entry_prefix,
                    patti_entry_counter=index.patti_entry_counter,
                    customer_ledger_prefix=index.customer_ledger_prefix,
                    customer_ledger_counter=index.customer_ledger_counter,
                    farmer_ledger_prefix=index.farmer_ledger_prefix,
                    farmer_ledger_counter=index.farmer_ledger_counter,
                    credit_bill_entry_prefix=index.credit_bill_entry_prefix,
                    credit_bill_entry_counter=index.credit_bill_entry_counter,
                    shilk_entry_prefix=index.shilk_entry_prefix,
                    shilk_entry_counter=index.shilk_entry_counter,
                    inventory_prefix=index.inventory_prefix,
                    inventory_counter=index.inventory_counter,
                )
        except OperationalError as error:
            raise CommandError(
                'Local Shop/Index SQL tables are not available in this environment. '
                'Run this backfill in the source-data environment that still contains shops_shop and shops_index.'
            ) from error

        if rows_written <= 0:
            raise CommandError('No Shop/Index metadata rows were available to backfill.')

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'Dry-run inspected {rows_written} shop metadata rows.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Backfilled {rows_written} shop metadata rows to Firestore.'))