from dataclasses import dataclass
import time

from django.conf import settings

from vegitable.firebase import initialize_project_firebase

from ..firebase_models.farmer_ledger import FarmerLedgerDocument
from ..models import FarmerLedger


def _normalize_contact(value):
    return ''.join(char for char in str(value) if char.isdigit()) or str(value).strip().lower()


@dataclass
class FarmerLedgerRecord:
    id: str | int | None
    shop_id: int
    name: str
    contact: str
    place: str
    created_at_ms: int


class FarmerLedgerRepository:
    def using_firebase(self):
        return settings.FIREBASE_ENABLED and settings.USE_FIREBASE_FARMER_LEDGER

    def create(self, *, shop_id, name, contact, place):
        if self.using_firebase():
            initialize_project_firebase()
            farmer = FarmerLedgerDocument(
                shop_id=str(shop_id),
                name=name,
                contact=contact,
                place=place,
                name_lower=name.strip().lower(),
                contact_normalized=_normalize_contact(contact),
                place_lower=place.strip().lower(),
                created_at_ms=int(time.time() * 1000),
            ).save()
            return self._from_firebase(farmer)

        farmer = FarmerLedger.objects.create(
            shop_id=shop_id,
            name=name,
            contact=contact,
            place=place,
        )
        return self._from_sql(farmer)

    def update(self, *, record_id, shop_id, name, contact, place):
        if self.using_firebase():
            initialize_project_firebase()
            farmer = FarmerLedgerDocument.get(str(record_id))
            if farmer is None:
                raise ValueError(f'FarmerLedger record {record_id} was not found in Firestore.')
            farmer.update(
                shop_id=str(shop_id),
                name=name,
                contact=contact,
                place=place,
                name_lower=name.strip().lower(),
                contact_normalized=_normalize_contact(contact),
                place_lower=place.strip().lower(),
            )
            return self._from_firebase(farmer)

        farmer = FarmerLedger.objects.get(pk=record_id)
        farmer.shop_id = shop_id
        farmer.name = name
        farmer.contact = contact
        farmer.place = place
        farmer.save()
        return self._from_sql(farmer)

    def get_by_id(self, record_id):
        if self.using_firebase():
            initialize_project_firebase()
            farmer = FarmerLedgerDocument.get(str(record_id))
            return None if farmer is None else self._from_firebase(farmer)

        farmer = FarmerLedger.objects.get(pk=record_id)
        return self._from_sql(farmer)

    def delete(self, record_id):
        if self.using_firebase():
            initialize_project_firebase()
            farmer = FarmerLedgerDocument.get(str(record_id))
            if farmer is None:
                return False
            farmer.delete()
            return True

        deleted, _ = FarmerLedger.objects.filter(pk=record_id).delete()
        return deleted > 0

    def list_by_shop(self, shop_id):
        if self.using_firebase():
            initialize_project_firebase()
            records = [
                self._from_firebase(item)
                for item in FarmerLedgerDocument.objects.filter(shop_id=str(shop_id))
            ]
            return sorted(records, key=lambda item: item.created_at_ms, reverse=True)

        return [
            self._from_sql(item)
            for item in FarmerLedger.objects.filter(shop_id=shop_id).order_by('-id')
        ]

    def exists_by_contact(self, contact):
        if self.using_firebase():
            initialize_project_firebase()
            normalized_contact = _normalize_contact(contact)
            return any(
                item.contact_normalized == normalized_contact
                for item in FarmerLedgerDocument.objects.all()
            )

        return FarmerLedger.objects.filter(contact=contact).exists()

    def search(self, *, shop_id, search_text):
        normalized_search = search_text.strip().lower()
        if self.using_firebase():
            records = self.list_by_shop(shop_id)
            return [
                record for record in records
                if normalized_search in record.name.lower()
                or normalized_search in record.contact.lower()
                or normalized_search in record.place.lower()
            ]

        queryset = FarmerLedger.objects.filter(shop_id=shop_id)
        results = queryset.filter(name__icontains=search_text) | queryset.filter(contact__icontains=search_text) | queryset.filter(place__icontains=search_text)
        return [self._from_sql(item) for item in results]

    @staticmethod
    def _from_sql(item):
        return FarmerLedgerRecord(
            id=item.pk,
            shop_id=item.shop.pk,
            name=item.name,
            contact=item.contact,
            place=item.place,
            created_at_ms=0,
        )

    @staticmethod
    def _from_firebase(item):
        return FarmerLedgerRecord(
            id=item.id,
            shop_id=int(item.shop_id),
            name=item.name,
            contact=item.contact,
            place=item.place,
            created_at_ms=int(item.created_at_ms or 0),
        )