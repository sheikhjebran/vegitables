from dataclasses import dataclass
import datetime
import time

from django.conf import settings

from vegitable.firebase import initialize_project_firebase

from ..firebase_models.credit_bill import CreditBillEntryDocument


@dataclass
class CreditBillHistoryRecord:
    date: str
    amount: float
    payment_mode: str


@dataclass
class CreditBillRecord:
    id: str | None
    shop_id: int
    customer_name: str
    sales_bill_record_id: str
    sales_bill_id: str
    initial_credit_bill_amount: float
    histories: list[CreditBillHistoryRecord]
    created_at_ms: int


class CreditBillRepository:
    def using_firebase(self):
        return (
            settings.FIREBASE_ENABLED
            and settings.USE_FIREBASE_SALES
            and settings.USE_FIREBASE_CREDIT
        )

    def list_by_shop(self, shop_id):
        initialize_project_firebase()
        records = [
            self._from_firebase(item)
            for item in CreditBillEntryDocument.objects.filter(shop_id=str(shop_id))
        ]
        return sorted(records, key=lambda item: item.created_at_ms, reverse=True)

    def get_by_id(self, record_id):
        initialize_project_firebase()
        document = CreditBillEntryDocument.get(str(record_id))
        return None if document is None else self._from_firebase(document)

    def get_by_sales_bill_record_id(self, shop_id, sales_bill_record_id):
        for record in self.list_by_shop(shop_id):
            if str(record.sales_bill_record_id) == str(sales_bill_record_id):
                return record
        return None

    def upsert_for_sales_bill(self, *, shop_id, customer_name, sales_bill_record_id, sales_bill_id, initial_credit_bill_amount):
        initialize_project_firebase()
        existing = self.get_by_sales_bill_record_id(shop_id, sales_bill_record_id)
        if existing is None:
            document = CreditBillEntryDocument(
                shop_id=str(shop_id),
                customer_name=customer_name,
                sales_bill_record_id=str(sales_bill_record_id),
                sales_bill_id=str(sales_bill_id),
                initial_credit_bill_amount=float(initial_credit_bill_amount),
                histories=[],
                created_at_ms=int(time.time() * 1000),
            ).save()
            return self._from_firebase(document)

        existing_document = CreditBillEntryDocument.get(str(existing.id))
        if existing_document is None:
            raise ValueError(f'Credit bill {existing.id} was not found in Firestore.')

        existing_document.update(
            customer_name=customer_name,
            sales_bill_id=str(sales_bill_id),
            initial_credit_bill_amount=float(initial_credit_bill_amount),
        )
        return self._from_firebase(existing_document)

    def import_legacy_record(self, *, shop_id, customer_name, sales_bill_record_id, sales_bill_id, initial_credit_bill_amount, histories, created_at_ms=None):
        initialize_project_firebase()
        serialized_histories = [self._serialize_history(history) for history in histories]
        document = CreditBillEntryDocument(
            shop_id=str(shop_id),
            customer_name=str(customer_name),
            sales_bill_record_id=str(sales_bill_record_id),
            sales_bill_id=str(sales_bill_id),
            initial_credit_bill_amount=float(initial_credit_bill_amount),
            histories=serialized_histories,
            created_at_ms=int(created_at_ms if created_at_ms is not None else time.time() * 1000),
        ).save()
        return self._from_firebase(document)

    def add_payment(self, *, credit_bill_record_id, amount, payment_mode, date=None):
        initialize_project_firebase()
        document = CreditBillEntryDocument.get(str(credit_bill_record_id))
        if document is None:
            raise ValueError(f'Credit bill {credit_bill_record_id} was not found in Firestore.')

        history_date = date or datetime.date.today().isoformat()
        histories = list(document.histories or [])
        histories.append({
            'date': str(history_date),
            'amount': float(amount),
            'payment_mode': str(payment_mode),
        })
        document.update(histories=histories)
        return self._from_firebase(document)

    def list_history(self, credit_bill_record_id):
        record = self.get_by_id(credit_bill_record_id)
        if record is None:
            return []
        return record.histories

    def delete(self, record_id):
        initialize_project_firebase()
        document = CreditBillEntryDocument.get(str(record_id))
        if document is None:
            return False
        document.delete()
        return True

    def _from_firebase(self, item):
        histories = [
            CreditBillHistoryRecord(
                date=str(history.get('date', '')),
                amount=float(history.get('amount', 0.0)),
                payment_mode=str(history.get('payment_mode', '')),
            )
            for history in list(item.histories or [])
        ]
        return CreditBillRecord(
            id=item.id,
            shop_id=int(item.shop_id),
            customer_name=str(item.customer_name),
            sales_bill_record_id=str(item.sales_bill_record_id),
            sales_bill_id=str(item.sales_bill_id),
            initial_credit_bill_amount=float(item.initial_credit_bill_amount),
            histories=histories,
            created_at_ms=int(item.created_at_ms or 0),
        )

    @staticmethod
    def _serialize_history(history):
        if isinstance(history, CreditBillHistoryRecord):
            return {
                'date': str(history.date),
                'amount': float(history.amount),
                'payment_mode': str(history.payment_mode),
            }

        return {
            'date': str(history.get('date', '')),
            'amount': float(history.get('amount', 0.0)),
            'payment_mode': str(history.get('payment_mode', '')),
        }
