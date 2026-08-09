from dataclasses import dataclass
import time

from django.conf import settings

from vegitable.firebase import initialize_project_firebase

from ..firebase_models.shop_metadata import ShopMetadataDocument


@dataclass
class ShopMetadataRecord:
    id: str | None
    owner_user_id: int
    shop_id: int
    shop_name: str
    shop_location: str
    shop_address: str
    expenditure_entry_prefix: str
    expenditure_entry_counter: int
    arrival_entry_prefix: str
    arrival_entry_counter: int
    sales_bill_entry_prefix: str
    sales_bill_entry_counter: int
    patti_entry_prefix: str
    patti_entry_counter: int
    customer_ledger_prefix: str
    customer_ledger_counter: int
    farmer_ledger_prefix: str
    farmer_ledger_counter: int
    credit_bill_entry_prefix: str
    credit_bill_entry_counter: int
    shilk_entry_prefix: str
    shilk_entry_counter: int
    inventory_prefix: str
    inventory_counter: int
    created_at_ms: int

    @property
    def pk(self):
        return self.shop_id


class ShopMetadataRepository:
    COUNTER_FIELDS = {
        'expenditure_entry_counter',
        'arrival_entry_counter',
        'sales_bill_entry_counter',
        'patti_entry_counter',
        'customer_ledger_counter',
        'farmer_ledger_counter',
        'credit_bill_entry_counter',
        'shilk_entry_counter',
        'inventory_counter',
    }

    PREFIX_FIELDS = {
        'expenditure_entry_prefix',
        'arrival_entry_prefix',
        'sales_bill_entry_prefix',
        'patti_entry_prefix',
        'customer_ledger_prefix',
        'farmer_ledger_prefix',
        'credit_bill_entry_prefix',
        'shilk_entry_prefix',
        'inventory_prefix',
    }

    def using_firebase(self):
        return settings.FIREBASE_ENABLED and settings.USE_FIREBASE_SHOP_METADATA

    def requirement_message(self):
        return 'Enable USE_FIREBASE_SHOP_METADATA=True and backfill shop/index metadata to Firebase. SQL shop/index path has been removed for this workflow.'

    def get_by_owner_user_id(self, owner_user_id):
        owner_user_id = self._resolve_owner_user_id(owner_user_id)
        self._ensure_enabled()
        initialize_project_firebase()
        results = list(ShopMetadataDocument.objects.filter(owner_user_id=str(owner_user_id)))
        if len(results) <= 0:
            return None
        return self._from_firebase(results[0])

    def require_by_owner_user_id(self, owner_user_id):
        owner_user_id = self._resolve_owner_user_id(owner_user_id)
        record = self.get_by_owner_user_id(owner_user_id)
        if record is None:
            self._bootstrap_from_sql(owner_user_id)
            record = self.get_by_owner_user_id(owner_user_id)
        if record is None:
            raise ValueError(
                f'Shop metadata for owner {owner_user_id} was not found in Firebase. '
                f'Create an Index row for that owner\'s shop or run backfill_shop_metadata_to_firebase.'
            )
        return record

    def create_or_update(
        self,
        *,
        owner_user_id,
        shop_id,
        shop_name,
        shop_location,
        shop_address,
        expenditure_entry_prefix,
        expenditure_entry_counter,
        arrival_entry_prefix,
        arrival_entry_counter,
        sales_bill_entry_prefix,
        sales_bill_entry_counter,
        patti_entry_prefix,
        patti_entry_counter,
        customer_ledger_prefix,
        customer_ledger_counter,
        farmer_ledger_prefix,
        farmer_ledger_counter,
        credit_bill_entry_prefix,
        credit_bill_entry_counter,
        shilk_entry_prefix,
        shilk_entry_counter,
        inventory_prefix,
        inventory_counter,
    ):
        self._ensure_enabled()
        initialize_project_firebase()
        existing = self.get_by_owner_user_id(owner_user_id)
        payload = {
            'owner_user_id': str(owner_user_id),
            'shop_id': int(shop_id),
            'shop_name': str(shop_name),
            'shop_location': str(shop_location),
            'shop_address': str(shop_address),
            'expenditure_entry_prefix': str(expenditure_entry_prefix),
            'expenditure_entry_counter': int(expenditure_entry_counter),
            'arrival_entry_prefix': str(arrival_entry_prefix),
            'arrival_entry_counter': int(arrival_entry_counter),
            'sales_bill_entry_prefix': str(sales_bill_entry_prefix),
            'sales_bill_entry_counter': int(sales_bill_entry_counter),
            'patti_entry_prefix': str(patti_entry_prefix),
            'patti_entry_counter': int(patti_entry_counter),
            'customer_ledger_prefix': str(customer_ledger_prefix),
            'customer_ledger_counter': int(customer_ledger_counter),
            'farmer_ledger_prefix': str(farmer_ledger_prefix),
            'farmer_ledger_counter': int(farmer_ledger_counter),
            'credit_bill_entry_prefix': str(credit_bill_entry_prefix),
            'credit_bill_entry_counter': int(credit_bill_entry_counter),
            'shilk_entry_prefix': str(shilk_entry_prefix),
            'shilk_entry_counter': int(shilk_entry_counter),
            'inventory_prefix': str(inventory_prefix),
            'inventory_counter': int(inventory_counter),
        }
        if existing is None:
            document = ShopMetadataDocument(
                **payload,
                created_at_ms=int(time.time() * 1000),
            ).save()
            return self._from_firebase(document)

        document = ShopMetadataDocument.get(existing.id)
        if document is None:
            raise ValueError(f'Shop metadata document {existing.id} was not found in Firestore.')
        document.update(**payload)
        return self._from_firebase(document)

    def update_prefixes(self, owner_user_id, **prefix_updates):
        invalid_fields = set(prefix_updates) - self.PREFIX_FIELDS
        if invalid_fields:
            raise ValueError(f'Unsupported prefix fields: {sorted(invalid_fields)}')

        record = self.require_by_owner_user_id(owner_user_id)
        document = ShopMetadataDocument.get(record.id)
        if document is None:
            raise ValueError(f'Shop metadata document {record.id} was not found in Firestore.')
        document.update(**{key: str(value) for key, value in prefix_updates.items()})
        return self._from_firebase(document)

    def increment_counter(self, owner_user_id, counter_field):
        if counter_field not in self.COUNTER_FIELDS:
            raise ValueError(f'Unsupported counter field: {counter_field}')

        record = self.require_by_owner_user_id(owner_user_id)
        document = ShopMetadataDocument.get(record.id)
        if document is None:
            raise ValueError(f'Shop metadata document {record.id} was not found in Firestore.')

        next_value = int(getattr(record, counter_field)) + 1
        document.update(**{counter_field: next_value})
        return self._from_firebase(document)

    def delete(self, record_id):
        self._ensure_enabled()
        initialize_project_firebase()
        document = ShopMetadataDocument.get(str(record_id))
        if document is None:
            return False
        document.delete()
        return True

    def _ensure_enabled(self):
        if not self.using_firebase():
            raise ValueError(self.requirement_message())

    @staticmethod
    def _resolve_owner_user_id(user_id):
        from ..models import Shop, ShopUserAssignment

        assignment = ShopUserAssignment.objects.select_related('shop').filter(
            user_id=user_id,
            is_active=True,
        ).first()
        if assignment is not None:
            return int(assignment.shop.shop_owner_id)

        owned_shop_exists = Shop.objects.filter(shop_owner_id=user_id).exists()
        if owned_shop_exists:
            return int(user_id)

        return int(user_id)

    def _bootstrap_from_sql(self, owner_user_id):
        from ..models import Index, Shop

        shop = Shop.objects.filter(shop_owner_id=owner_user_id).first()
        if shop is None:
            return

        index = Index.objects.filter(shop=shop).first()
        if index is None:
            return

        self.create_or_update(
            owner_user_id=owner_user_id,
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

    @staticmethod
    def _from_firebase(document):
        return ShopMetadataRecord(
            id=document.id,
            owner_user_id=int(document.owner_user_id),
            shop_id=int(document.shop_id),
            shop_name=str(document.shop_name),
            shop_location=str(document.shop_location),
            shop_address=str(document.shop_address),
            expenditure_entry_prefix=str(document.expenditure_entry_prefix),
            expenditure_entry_counter=int(document.expenditure_entry_counter),
            arrival_entry_prefix=str(document.arrival_entry_prefix),
            arrival_entry_counter=int(document.arrival_entry_counter),
            sales_bill_entry_prefix=str(document.sales_bill_entry_prefix),
            sales_bill_entry_counter=int(document.sales_bill_entry_counter),
            patti_entry_prefix=str(document.patti_entry_prefix),
            patti_entry_counter=int(document.patti_entry_counter),
            customer_ledger_prefix=str(document.customer_ledger_prefix),
            customer_ledger_counter=int(document.customer_ledger_counter),
            farmer_ledger_prefix=str(document.farmer_ledger_prefix),
            farmer_ledger_counter=int(document.farmer_ledger_counter),
            credit_bill_entry_prefix=str(document.credit_bill_entry_prefix),
            credit_bill_entry_counter=int(document.credit_bill_entry_counter),
            shilk_entry_prefix=str(document.shilk_entry_prefix),
            shilk_entry_counter=int(document.shilk_entry_counter),
            inventory_prefix=str(document.inventory_prefix),
            inventory_counter=int(document.inventory_counter),
            created_at_ms=int(getattr(document, 'created_at_ms', 0) or 0),
        )