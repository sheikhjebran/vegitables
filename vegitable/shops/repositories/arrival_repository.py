from dataclasses import dataclass
import time
from uuid import uuid4

from django.conf import settings

from vegitable.firebase import initialize_project_firebase

from ..firebase_models.arrival import ArrivalEntryDocument


@dataclass
class ArrivalGoodsRecord:
    local_id: str
    former_name: str
    item_name: str
    initial_qty: int
    qty: int
    weight: float
    remarks: str
    advance: float
    patti_status: bool

    @property
    def id(self):
        return self.local_id

    @property
    def pk(self):
        return self.local_id


@dataclass
class ArrivalEntryRecord:
    id: str | None
    shop_id: int
    arrival_id: str
    gp_no: str
    lorry_no: str
    date: str
    patti_name: str
    total_bags: int
    empty_data: bool
    goods: list[ArrivalGoodsRecord]
    created_at_ms: int


class ArrivalRepository:
    def using_firebase(self):
        return settings.FIREBASE_ENABLED and settings.USE_FIREBASE_ARRIVAL

    def create(self, *, shop_id, arrival_id, gp_no, lorry_no, date, patti_name, total_bags, empty_data, goods):
        initialize_project_firebase()
        document = ArrivalEntryDocument(
            shop_id=str(shop_id),
            arrival_id=arrival_id,
            gp_no=gp_no,
            lorry_no=lorry_no,
            date=date,
            patti_name=patti_name,
            total_bags=int(total_bags),
            empty_data=bool(empty_data),
            goods=[self._serialize_goods(item) for item in goods],
            created_at_ms=int(time.time() * 1000),
        ).save()
        return self._from_firebase(document)

    def update(self, *, record_id, shop_id, arrival_id, gp_no, lorry_no, date, patti_name, total_bags, empty_data, goods):
        initialize_project_firebase()
        document = ArrivalEntryDocument.get(str(record_id))
        if document is None:
            raise ValueError(f'Arrival record {record_id} was not found in Firestore.')
        document.update(
            shop_id=str(shop_id),
            arrival_id=arrival_id,
            gp_no=gp_no,
            lorry_no=lorry_no,
            date=date,
            patti_name=patti_name,
            total_bags=int(total_bags),
            empty_data=bool(empty_data),
            goods=[self._serialize_goods(item) for item in goods],
        )
        return self._from_firebase(document)

    def get_by_id(self, record_id):
        initialize_project_firebase()
        document = ArrivalEntryDocument.get(str(record_id))
        return None if document is None else self._from_firebase(document)

    def list_by_shop(self, shop_id):
        initialize_project_firebase()
        records = [
            self._from_firebase(item)
            for item in ArrivalEntryDocument.objects.filter(shop_id=str(shop_id))
        ]
        return sorted(records, key=lambda item: item.created_at_ms, reverse=True)

    def list_non_empty_by_shop(self, shop_id):
        return [record for record in self.list_by_shop(shop_id) if not record.empty_data]

    def find_duplicate(self, *, shop_id, lorry_no, date):
        initialize_project_firebase()
        records = [
            self._from_firebase(item)
            for item in ArrivalEntryDocument.objects.filter(shop_id=str(shop_id), lorry_no=lorry_no, date=date)
        ]
        return records

    def delete(self, record_id):
        initialize_project_firebase()
        document = ArrivalEntryDocument.get(str(record_id))
        if document is None:
            return False
        document.delete()
        return True

    def list_available_goods_by_shop(self, shop_id):
        available = []
        for entry in self.list_by_shop(shop_id):
            for goods in entry.goods:
                if goods.qty >= 1:
                    available.append((entry, goods))
        return available

    def get_goods_by_local_id(self, shop_id, local_id):
        for entry, goods in self.list_available_goods_by_shop(shop_id):
            if str(goods.local_id) == str(local_id):
                return entry, goods
        return None, None

    def get_goods_by_local_id_any_status(self, shop_id, local_id):
        for entry in self.list_by_shop(shop_id):
            for goods in entry.goods:
                if str(goods.local_id) == str(local_id):
                    return entry, goods
        return None, None

    def update_goods_quantity(self, *, shop_id, local_id, new_qty):
        entry, goods = self.get_goods_by_local_id_any_status(shop_id, local_id)
        if entry is None or goods is None:
            raise ValueError(f'Arrival goods {local_id} was not found in Firestore.')

        updated_goods = []
        for item in entry.goods:
            if str(item.local_id) == str(local_id):
                updated_goods.append(ArrivalGoodsRecord(
                    local_id=item.local_id,
                    former_name=item.former_name,
                    item_name=item.item_name,
                    initial_qty=item.initial_qty,
                    qty=int(new_qty),
                    weight=item.weight,
                    remarks=item.remarks,
                    advance=item.advance,
                    patti_status=item.patti_status,
                ))
            else:
                updated_goods.append(item)

        return self.update(
            record_id=entry.id,
            shop_id=entry.shop_id,
            arrival_id=entry.arrival_id,
            gp_no=entry.gp_no,
            lorry_no=entry.lorry_no,
            date=entry.date,
            patti_name=entry.patti_name,
            total_bags=entry.total_bags,
            empty_data=entry.empty_data,
            goods=updated_goods,
        )

    def build_inventory_entries(self, shop_id):
        entries = []
        for entry, goods in self.list_available_goods_by_shop(shop_id):
            entries.append({
                'id': goods.local_id,
                'arrival_entry__date': entry.date,
                'remarks': goods.remarks,
                'item_name': goods.item_name,
                'initial_qty': goods.initial_qty,
                'qty': goods.qty,
                'sold': goods.initial_qty - goods.qty,
                'balance': goods.qty,
            })
        return entries

    def _serialize_goods(self, goods):
        if isinstance(goods, ArrivalGoodsRecord):
            return {
                'local_id': goods.local_id,
                'former_name': goods.former_name,
                'item_name': goods.item_name,
                'initial_qty': int(goods.initial_qty),
                'qty': int(goods.qty),
                'weight': float(goods.weight),
                'remarks': goods.remarks,
                'advance': float(goods.advance),
                'patti_status': bool(goods.patti_status),
            }

        return {
            'local_id': str(goods.get('local_id') or uuid4().hex[:12]),
            'former_name': goods.get('former_name', ''),
            'item_name': goods.get('item_name', ''),
            'initial_qty': int(goods.get('initial_qty', 0)),
            'qty': int(goods.get('qty', 0)),
            'weight': float(goods.get('weight', 0.0)),
            'remarks': goods.get('remarks', ''),
            'advance': float(goods.get('advance', 0.0)),
            'patti_status': bool(goods.get('patti_status', False)),
        }

    def _from_firebase(self, item):
        goods = [
            ArrivalGoodsRecord(
                local_id=str(goods_item.get('local_id', '')),
                former_name=str(goods_item.get('former_name', '')),
                item_name=str(goods_item.get('item_name', '')),
                initial_qty=int(goods_item.get('initial_qty', 0)),
                qty=int(goods_item.get('qty', 0)),
                weight=float(goods_item.get('weight', 0.0)),
                remarks=str(goods_item.get('remarks', '')),
                advance=float(goods_item.get('advance', 0.0)),
                patti_status=bool(goods_item.get('patti_status', False)),
            )
            for goods_item in list(item.goods or [])
        ]
        return ArrivalEntryRecord(
            id=item.id,
            shop_id=int(item.shop_id),
            arrival_id=str(item.arrival_id),
            gp_no=str(item.gp_no),
            lorry_no=str(item.lorry_no),
            date=str(item.date),
            patti_name=str(item.patti_name),
            total_bags=int(item.total_bags),
            empty_data=bool(item.empty_data),
            goods=goods,
            created_at_ms=int(item.created_at_ms or 0),
        )