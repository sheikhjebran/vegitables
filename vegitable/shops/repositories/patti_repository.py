from dataclasses import dataclass
import datetime
import time

from django.conf import settings

from vegitable.firebase import initialize_project_firebase

from ..firebase_models.patti import PattiEntryDocument
from ..models import PattiEntry, PattiEntryList


@dataclass
class PattiEntryItemRecord:
    item: str
    lot_no: str
    weight: str
    rate: str
    amount: float


@dataclass
class PattiEntryRecord:
    id: str | int | None
    shop_id: int
    patti_id: str
    lorry_no: str
    date: datetime.date
    advance: float
    farmer_name: str
    total_weight: float
    hamali: float
    net_amount: float
    items: list[PattiEntryItemRecord]
    created_at_ms: int


class PattiRepository:
    def using_firebase(self):
        return settings.FIREBASE_ENABLED and settings.USE_FIREBASE_PATTI

    def create(self, *, shop_id, patti_id, lorry_no, date, advance, farmer_name, total_weight, hamali, net_amount, items):
        if self.using_firebase():
            initialize_project_firebase()
            document = PattiEntryDocument(
                shop_id=str(shop_id),
                patti_id=str(patti_id),
                lorry_no=str(lorry_no),
                date=self._date_to_iso(date),
                advance=float(advance),
                farmer_name=str(farmer_name),
                total_weight=float(total_weight),
                hamali=float(hamali),
                net_amount=float(net_amount),
                items=[self._serialize_item(item) for item in items],
                created_at_ms=int(time.time() * 1000),
            ).save()
            return self._from_firebase(document)

        entry = PattiEntry.objects.create(
            shop_id=shop_id,
            patti_id=str(patti_id),
            lorry_no=str(lorry_no),
            date=self._coerce_date(date),
            advance=float(advance),
            farmer_name=str(farmer_name),
            total_weight=float(total_weight),
            hamali=float(hamali),
            net_amount=float(net_amount),
        )
        for item in items:
            row = self._coerce_item(item)
            PattiEntryList.objects.create(
                item=row.item,
                lot_no=row.lot_no,
                weight=row.weight,
                rate=row.rate,
                amount=float(row.amount),
                patti=entry,
            )
        return self._from_sql(entry)

    def update(self, *, record_id, shop_id, patti_id, lorry_no, date, advance, farmer_name, total_weight, hamali, net_amount, items):
        if self.using_firebase():
            initialize_project_firebase()
            document = PattiEntryDocument.get(str(record_id))
            if document is None:
                raise ValueError(f'Patti record {record_id} was not found in Firestore.')

            document.update(
                shop_id=str(shop_id),
                patti_id=str(patti_id),
                lorry_no=str(lorry_no),
                date=self._date_to_iso(date),
                advance=float(advance),
                farmer_name=str(farmer_name),
                total_weight=float(total_weight),
                hamali=float(hamali),
                net_amount=float(net_amount),
                items=[self._serialize_item(item) for item in items],
            )
            return self._from_firebase(document)

        entry = PattiEntry.objects.get(pk=record_id)
        entry.shop_id = shop_id
        entry.patti_id = str(patti_id)
        entry.lorry_no = str(lorry_no)
        entry.date = self._coerce_date(date)
        entry.advance = float(advance)
        entry.farmer_name = str(farmer_name)
        entry.total_weight = float(total_weight)
        entry.hamali = float(hamali)
        entry.net_amount = float(net_amount)
        entry.save()

        PattiEntryList.objects.filter(patti=entry).delete()
        for item in items:
            row = self._coerce_item(item)
            PattiEntryList.objects.create(
                item=row.item,
                lot_no=row.lot_no,
                weight=row.weight,
                rate=row.rate,
                amount=float(row.amount),
                patti=entry,
            )
        return self._from_sql(entry)

    def list_by_shop(self, shop_id):
        if self.using_firebase():
            initialize_project_firebase()
            records = [
                self._from_firebase(item)
                for item in PattiEntryDocument.objects.filter(shop_id=str(shop_id))
            ]
            return sorted(records, key=lambda item: item.created_at_ms, reverse=True)

        return [
            self._from_sql(item)
            for item in PattiEntry.objects.filter(shop_id=shop_id).order_by('-id')
        ]

    def get_by_id(self, record_id):
        if self.using_firebase():
            initialize_project_firebase()
            item = PattiEntryDocument.get(str(record_id))
            return None if item is None else self._from_firebase(item)

        entry = PattiEntry.objects.get(pk=record_id)
        return self._from_sql(entry)

    def delete(self, record_id):
        if self.using_firebase():
            initialize_project_firebase()
            item = PattiEntryDocument.get(str(record_id))
            if item is None:
                return False
            item.delete()
            return True

        deleted, _ = PattiEntry.objects.filter(pk=record_id).delete()
        return deleted > 0

    @staticmethod
    def _coerce_date(value):
        if isinstance(value, datetime.date):
            return value
        return datetime.date.fromisoformat(str(value))

    @staticmethod
    def _date_to_iso(value):
        if isinstance(value, datetime.date):
            return value.isoformat()
        return str(value)

    @staticmethod
    def _coerce_item(item):
        if isinstance(item, PattiEntryItemRecord):
            return item
        return PattiEntryItemRecord(
            item=str(item.get('item', '')),
            lot_no=str(item.get('lot_no', '')),
            weight=str(item.get('weight', '0')),
            rate=str(item.get('rate', '0')),
            amount=float(item.get('amount', 0.0)),
        )

    def _serialize_item(self, item):
        row = self._coerce_item(item)
        return {
            'item': row.item,
            'lot_no': row.lot_no,
            'weight': row.weight,
            'rate': row.rate,
            'amount': float(row.amount),
        }

    @staticmethod
    def _from_sql(item):
        rows = PattiEntryList.objects.filter(patti=item)
        return PattiEntryRecord(
            id=item.pk,
            shop_id=item.shop.pk,
            patti_id=item.patti_id,
            lorry_no=item.lorry_no,
            date=item.date,
            advance=float(item.advance),
            farmer_name=item.farmer_name,
            total_weight=float(item.total_weight),
            hamali=float(item.hamali),
            net_amount=float(item.net_amount),
            items=[
                PattiEntryItemRecord(
                    item=row.item,
                    lot_no=row.lot_no,
                    weight=str(row.weight),
                    rate=str(row.rate),
                    amount=float(row.amount),
                )
                for row in rows
            ],
            created_at_ms=0,
        )

    @staticmethod
    def _from_firebase(item):
        date_value = str(item.date)
        return PattiEntryRecord(
            id=item.id,
            shop_id=int(item.shop_id),
            patti_id=str(item.patti_id),
            lorry_no=str(item.lorry_no),
            date=datetime.date.fromisoformat(date_value),
            advance=float(item.advance),
            farmer_name=str(item.farmer_name),
            total_weight=float(item.total_weight),
            hamali=float(item.hamali),
            net_amount=float(item.net_amount),
            items=[
                PattiEntryItemRecord(
                    item=str(row.get('item', '')),
                    lot_no=str(row.get('lot_no', '')),
                    weight=str(row.get('weight', '0')),
                    rate=str(row.get('rate', '0')),
                    amount=float(row.get('amount', 0.0)),
                )
                for row in list(item.items or [])
            ],
            created_at_ms=int(item.created_at_ms or 0),
        )
