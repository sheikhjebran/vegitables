from dataclasses import dataclass
import time

from django.conf import settings

from vegitable.firebase import initialize_project_firebase

from ..firebase_models.customer_ledger import CustomerLedgerDocument
from ..models import CustomerLedger


def _normalize_contact(value):
    return ''.join(char for char in str(value) if char.isdigit()) or str(value).strip().lower()


@dataclass
class CustomerLedgerRecord:
    id: str | int | None
    shop_id: int
    name: str
    contact: str
    address: str
    created_at_ms: int


class CustomerLedgerRepository:
    def using_firebase(self):
        return settings.FIREBASE_ENABLED and settings.USE_FIREBASE_CUSTOMER_LEDGER

    def create(self, *, shop_id, name, contact, address):
        if self.using_firebase():
            initialize_project_firebase()
            customer = CustomerLedgerDocument(
                shop_id=str(shop_id),
                name=name,
                contact=contact,
                address=address,
                name_lower=name.strip().lower(),
                contact_normalized=_normalize_contact(contact),
                address_lower=address.strip().lower(),
                created_at_ms=int(time.time() * 1000),
            ).save()
            return self._from_firebase(customer)

        customer = CustomerLedger.objects.create(
            shop_id=shop_id,
            name=name,
            contact=contact,
            address=address,
        )
        return self._from_sql(customer)

    def update(self, *, record_id, shop_id, name, contact, address):
        if self.using_firebase():
            initialize_project_firebase()
            customer = CustomerLedgerDocument.get(str(record_id))
            if customer is None:
                raise ValueError(f'CustomerLedger record {record_id} was not found in Firestore.')
            customer.update(
                shop_id=str(shop_id),
                name=name,
                contact=contact,
                address=address,
                name_lower=name.strip().lower(),
                contact_normalized=_normalize_contact(contact),
                address_lower=address.strip().lower(),
            )
            return self._from_firebase(customer)

        customer = CustomerLedger.objects.get(pk=record_id)
        customer.shop_id = shop_id
        customer.name = name
        customer.contact = contact
        customer.address = address
        customer.save()
        return self._from_sql(customer)

    def get_by_id(self, record_id):
        if self.using_firebase():
            initialize_project_firebase()
            customer = CustomerLedgerDocument.get(str(record_id))
            return None if customer is None else self._from_firebase(customer)

        customer = CustomerLedger.objects.get(pk=record_id)
        return self._from_sql(customer)

    def delete(self, record_id):
        if self.using_firebase():
            initialize_project_firebase()
            customer = CustomerLedgerDocument.get(str(record_id))
            if customer is None:
                return False
            customer.delete()
            return True

        deleted, _ = CustomerLedger.objects.filter(pk=record_id).delete()
        return deleted > 0

    def list_by_shop(self, shop_id):
        if self.using_firebase():
            initialize_project_firebase()
            records = [
                self._from_firebase(item)
                for item in CustomerLedgerDocument.objects.filter(shop_id=str(shop_id))
            ]
            return sorted(records, key=lambda item: item.created_at_ms, reverse=True)

        return [
            self._from_sql(item)
            for item in CustomerLedger.objects.filter(shop_id=shop_id).order_by('-id')
        ]

    def exists_by_contact(self, *, shop_id, contact):
        if self.using_firebase():
            initialize_project_firebase()
            normalized_contact = _normalize_contact(contact)
            return any(
                item.contact_normalized == normalized_contact
                for item in CustomerLedgerDocument.objects.filter(shop_id=str(shop_id))
            )

        return CustomerLedger.objects.filter(shop_id=shop_id, contact=contact).exists()

    def search(self, *, shop_id, search_text):
        normalized_search = search_text.strip().lower()
        if self.using_firebase():
            records = self.list_by_shop(shop_id)
            return [
                record for record in records
                if normalized_search in record.name.lower()
                or normalized_search in record.contact.lower()
                or normalized_search in record.address.lower()
            ]

        queryset = CustomerLedger.objects.filter(shop_id=shop_id)
        results = queryset.filter(name__icontains=search_text) | queryset.filter(contact__icontains=search_text) | queryset.filter(address__icontains=search_text)
        return [self._from_sql(item) for item in results]

    @staticmethod
    def _from_sql(item):
        return CustomerLedgerRecord(
            id=item.pk,
            shop_id=item.shop.pk,
            name=item.name,
            contact=item.contact,
            address=item.address,
            created_at_ms=0,
        )

    @staticmethod
    def _from_firebase(item):
        return CustomerLedgerRecord(
            id=item.id,
            shop_id=int(item.shop_id),
            name=item.name,
            contact=item.contact,
            address=item.address,
            created_at_ms=int(item.created_at_ms or 0),
        )