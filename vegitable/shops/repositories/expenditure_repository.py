from dataclasses import dataclass
import datetime
import time

from django.conf import settings

from vegitable.firebase import initialize_project_firebase

from ..firebase_models.expenditure import ExpenditureEntryDocument
from ..models import ExpenditureEntry


@dataclass
class ExpenditureRecord:
    id: str | int | None
    shop_id: int
    date: datetime.date
    expense_type: str
    amount: float
    remark: str
    empty_data: bool
    created_at_ms: int


class ExpenditureRepository:
    def using_firebase(self):
        return settings.FIREBASE_ENABLED and settings.USE_FIREBASE_EXPENDITURE

    def create(self, *, shop_id, date, expense_type, amount, remark, empty_data=False):
        if self.using_firebase():
            initialize_project_firebase()
            item = ExpenditureEntryDocument(
                shop_id=str(shop_id),
                date=self._date_to_iso(date),
                expense_type=str(expense_type),
                amount=float(amount),
                remark=str(remark),
                empty_data=bool(empty_data),
                created_at_ms=int(time.time() * 1000),
            ).save()
            return self._from_firebase(item)

        item = ExpenditureEntry.objects.create(
            shop_id=shop_id,
            date=self._coerce_date(date),
            expense_type=str(expense_type),
            amount=float(amount),
            remark=str(remark),
            Empty_data=bool(empty_data),
        )
        return self._from_sql(item)

    def update(self, *, record_id, shop_id, date, expense_type, amount, remark, empty_data=False):
        if self.using_firebase():
            initialize_project_firebase()
            item = ExpenditureEntryDocument.get(str(record_id))
            if item is None:
                raise ValueError(f'Expenditure record {record_id} was not found in Firestore.')
            item.update(
                shop_id=str(shop_id),
                date=self._date_to_iso(date),
                expense_type=str(expense_type),
                amount=float(amount),
                remark=str(remark),
                empty_data=bool(empty_data),
            )
            return self._from_firebase(item)

        item = ExpenditureEntry.objects.get(pk=record_id)
        item.shop_id = shop_id
        item.date = self._coerce_date(date)
        item.expense_type = str(expense_type)
        item.amount = float(amount)
        item.remark = str(remark)
        item.Empty_data = bool(empty_data)
        item.save()
        return self._from_sql(item)

    def get_by_id(self, record_id):
        if self.using_firebase():
            initialize_project_firebase()
            item = ExpenditureEntryDocument.get(str(record_id))
            return None if item is None else self._from_firebase(item)

        item = ExpenditureEntry.objects.get(pk=record_id)
        return self._from_sql(item)

    def delete(self, record_id):
        if self.using_firebase():
            initialize_project_firebase()
            item = ExpenditureEntryDocument.get(str(record_id))
            if item is None:
                return False
            item.delete()
            return True

        deleted, _ = ExpenditureEntry.objects.filter(pk=record_id).delete()
        return deleted > 0

    def list_by_shop(self, shop_id):
        if self.using_firebase():
            initialize_project_firebase()
            items = [
                self._from_firebase(item)
                for item in ExpenditureEntryDocument.objects.filter(shop_id=str(shop_id))
            ]
            return sorted(items, key=lambda item: item.created_at_ms, reverse=True)

        return [
            self._from_sql(item)
            for item in ExpenditureEntry.objects.filter(shop_id=shop_id).order_by('-id')
        ]

    def list_by_shop_and_date(self, shop_id, selected_date):
        selected_date_iso = self._date_to_iso(selected_date)
        if self.using_firebase():
            return [
                item for item in self.list_by_shop(shop_id)
                if item.date.isoformat() == selected_date_iso
            ]

        return [
            self._from_sql(item)
            for item in ExpenditureEntry.objects.filter(
                shop_id=shop_id,
                date=self._coerce_date(selected_date),
            ).order_by('-id')
        ]

    def sum_amount_by_shop_and_date(self, shop_id, selected_date):
        rows = self.list_by_shop_and_date(shop_id, selected_date)
        return sum(float(item.amount) for item in rows)

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
    def _from_sql(item):
        return ExpenditureRecord(
            id=item.pk,
            shop_id=item.shop_id,
            date=item.date,
            expense_type=item.expense_type,
            amount=float(item.amount),
            remark=item.remark,
            empty_data=bool(item.Empty_data),
            created_at_ms=0,
        )

    @staticmethod
    def _from_firebase(item):
        return ExpenditureRecord(
            id=item.id,
            shop_id=int(item.shop_id),
            date=datetime.date.fromisoformat(str(item.date)),
            expense_type=str(item.expense_type),
            amount=float(item.amount),
            remark=str(item.remark),
            empty_data=bool(item.empty_data),
            created_at_ms=int(item.created_at_ms or 0),
        )
