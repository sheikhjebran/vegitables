from dataclasses import dataclass
import time

from django.conf import settings

from vegitable.firebase import initialize_project_firebase

from ..firebase_models.sales_bill import SalesBillEntryDocument
from .arrival_repository import ArrivalRepository


@dataclass
class SalesBillItemRecord:
    arrival_entry_id: str
    arrival_goods_local_id: str
    item_name: str
    bags: int
    net_weight: float
    rates: float
    amount: float


@dataclass
class SalesBillRecord:
    id: str | None
    shop_id: int
    sales_bill_id: str
    payment_type: str
    customer_name: str
    date: str
    rmc: float
    commission: float
    cooli: float
    total_amount: float
    paid_amount: float
    balance_amount: float
    empty_data: bool
    items: list[SalesBillItemRecord]
    created_at_ms: int

    @property
    def total_net_weight(self):
        return sum(item.net_weight for item in self.items)


class SalesBillRepository:
    def __init__(self):
        self.arrival_repository = ArrivalRepository()

    def using_firebase(self):
        return settings.FIREBASE_ENABLED and settings.USE_FIREBASE_SALES and settings.USE_FIREBASE_ARRIVAL

    def create(self, *, shop_id, sales_bill_id, payment_type, customer_name, date, rmc, commission, cooli, total_amount, paid_amount, balance_amount, empty_data, items):
        initialize_project_firebase()
        serialized_items = [self._serialize_item(item) for item in items]
        original_quantities = []
        try:
            for item in serialized_items:
                entry, goods = self.arrival_repository.get_goods_by_local_id_any_status(shop_id, item['arrival_goods_local_id'])
                if entry is None or goods is None:
                    raise ValueError(f"Arrival goods {item['arrival_goods_local_id']} was not found.")
                if goods.qty < item['bags']:
                    raise ValueError(f"Arrival goods {item['arrival_goods_local_id']} has insufficient qty.")
                original_quantities.append((item['arrival_goods_local_id'], goods.qty))
                self.arrival_repository.update_goods_quantity(
                    shop_id=shop_id,
                    local_id=item['arrival_goods_local_id'],
                    new_qty=goods.qty - item['bags'],
                )

            document = SalesBillEntryDocument(
                shop_id=str(shop_id),
                sales_bill_id=sales_bill_id,
                payment_type=payment_type,
                customer_name=customer_name,
                date=date,
                rmc=float(rmc),
                commission=float(commission),
                cooli=float(cooli),
                total_amount=float(total_amount),
                paid_amount=float(paid_amount),
                balance_amount=float(balance_amount),
                empty_data=bool(empty_data),
                items=serialized_items,
                created_at_ms=int(time.time() * 1000),
            ).save()
            return self._from_firebase(document)
        except Exception:
            for local_id, qty in original_quantities:
                try:
                    self.arrival_repository.update_goods_quantity(shop_id=shop_id, local_id=local_id, new_qty=qty)
                except Exception:
                    pass
            raise

    def update(self, *, record_id, shop_id, sales_bill_id, payment_type, customer_name, date, rmc, commission, cooli, total_amount, paid_amount, balance_amount, empty_data, items):
        initialize_project_firebase()
        document = SalesBillEntryDocument.get(str(record_id))
        if document is None:
            raise ValueError(f'Sales bill {record_id} was not found in Firestore.')

        existing_record = self._from_firebase(document)
        serialized_items = [self._serialize_item(item) for item in items]

        old_quantities = {}
        for item in existing_record.items:
            old_quantities[item.arrival_goods_local_id] = old_quantities.get(item.arrival_goods_local_id, 0) + int(item.bags)

        new_quantities = {}
        for item in serialized_items:
            local_id = str(item['arrival_goods_local_id'])
            new_quantities[local_id] = new_quantities.get(local_id, 0) + int(item['bags'])

        affected_local_ids = set(old_quantities.keys()) | set(new_quantities.keys())
        original_stock = {}
        current_stock = {}
        try:
            for local_id in affected_local_ids:
                entry, goods = self.arrival_repository.get_goods_by_local_id_any_status(shop_id, local_id)
                if entry is None or goods is None:
                    raise ValueError(f'Arrival goods {local_id} was not found.')
                original_stock[local_id] = goods.qty
                current_stock[local_id] = goods.qty

            for local_id in affected_local_ids:
                old_bags = old_quantities.get(local_id, 0)
                new_bags = new_quantities.get(local_id, 0)
                delta = new_bags - old_bags
                if delta == 0:
                    continue

                current_qty = current_stock[local_id]
                if delta > 0:
                    if current_qty < delta:
                        raise ValueError(f'Arrival goods {local_id} has insufficient qty for update.')
                    self.arrival_repository.update_goods_quantity(
                        shop_id=shop_id,
                        local_id=local_id,
                        new_qty=current_qty - delta,
                    )
                    current_stock[local_id] = current_qty - delta
                else:
                    self.arrival_repository.update_goods_quantity(
                        shop_id=shop_id,
                        local_id=local_id,
                        new_qty=current_qty + abs(delta),
                    )
                    current_stock[local_id] = current_qty + abs(delta)

            document.update(
                shop_id=str(shop_id),
                sales_bill_id=sales_bill_id,
                payment_type=payment_type,
                customer_name=customer_name,
                date=date,
                rmc=float(rmc),
                commission=float(commission),
                cooli=float(cooli),
                total_amount=float(total_amount),
                paid_amount=float(paid_amount),
                balance_amount=float(balance_amount),
                empty_data=bool(empty_data),
                items=serialized_items,
            )
            return self._from_firebase(document)
        except Exception:
            for local_id, qty in original_stock.items():
                try:
                    self.arrival_repository.update_goods_quantity(shop_id=shop_id, local_id=local_id, new_qty=qty)
                except Exception:
                    pass
            raise

    def get_by_id(self, record_id):
        initialize_project_firebase()
        document = SalesBillEntryDocument.get(str(record_id))
        return None if document is None else self._from_firebase(document)

    def list_by_shop(self, shop_id):
        initialize_project_firebase()
        records = [
            self._from_firebase(item)
            for item in SalesBillEntryDocument.objects.filter(shop_id=str(shop_id))
        ]
        return sorted(records, key=lambda item: item.created_at_ms, reverse=True)

    def delete(self, record_id, restore_stock=True):
        initialize_project_firebase()
        document = SalesBillEntryDocument.get(str(record_id))
        if document is None:
            return False
        record = self._from_firebase(document)
        if restore_stock:
            for item in record.items:
                entry, goods = self.arrival_repository.get_goods_by_local_id_any_status(record.shop_id, item.arrival_goods_local_id)
                if entry is not None and goods is not None:
                    self.arrival_repository.update_goods_quantity(
                        shop_id=record.shop_id,
                        local_id=item.arrival_goods_local_id,
                        new_qty=goods.qty + item.bags,
                    )
        document.delete()
        return True

    def _serialize_item(self, item):
        if isinstance(item, SalesBillItemRecord):
            return {
                'arrival_entry_id': item.arrival_entry_id,
                'arrival_goods_local_id': item.arrival_goods_local_id,
                'item_name': item.item_name,
                'bags': int(item.bags),
                'net_weight': float(item.net_weight),
                'rates': float(item.rates),
                'amount': float(item.amount),
            }

        return {
            'arrival_entry_id': str(item.get('arrival_entry_id', '')),
            'arrival_goods_local_id': str(item.get('arrival_goods_local_id', '')),
            'item_name': str(item.get('item_name', '')),
            'bags': int(item.get('bags', 0)),
            'net_weight': float(item.get('net_weight', 0.0)),
            'rates': float(item.get('rates', 0.0)),
            'amount': float(item.get('amount', 0.0)),
        }

    def _from_firebase(self, item):
        items = [
            SalesBillItemRecord(
                arrival_entry_id=str(line.get('arrival_entry_id', '')),
                arrival_goods_local_id=str(line.get('arrival_goods_local_id', '')),
                item_name=str(line.get('item_name', '')),
                bags=int(line.get('bags', 0)),
                net_weight=float(line.get('net_weight', 0.0)),
                rates=float(line.get('rates', 0.0)),
                amount=float(line.get('amount', 0.0)),
            )
            for line in list(item.items or [])
        ]
        return SalesBillRecord(
            id=item.id,
            shop_id=int(item.shop_id),
            sales_bill_id=str(item.sales_bill_id),
            payment_type=str(item.payment_type),
            customer_name=str(item.customer_name),
            date=str(item.date),
            rmc=float(item.rmc),
            commission=float(item.commission),
            cooli=float(item.cooli),
            total_amount=float(item.total_amount),
            paid_amount=float(item.paid_amount),
            balance_amount=float(item.balance_amount),
            empty_data=bool(item.empty_data),
            items=items,
            created_at_ms=int(item.created_at_ms or 0),
        )