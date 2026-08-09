from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Index, Shop
from .repositories.shop_metadata_repository import ShopMetadataRepository


shop_metadata_repository = ShopMetadataRepository()


def _sync_shop_metadata(shop):
    if not shop_metadata_repository.using_firebase():
        return

    index = Index.objects.filter(shop=shop).first()
    if index is None:
        return

    shop_metadata_repository.create_or_update(
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


@receiver(post_save, sender=Shop)
def sync_shop_metadata_from_shop(sender, instance, **kwargs):
    _sync_shop_metadata(instance)


@receiver(post_save, sender=Index)
def sync_shop_metadata_from_index(sender, instance, **kwargs):
    _sync_shop_metadata(instance.shop)