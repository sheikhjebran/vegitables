from dataclasses import dataclass

from django.conf import settings

from vegitable.firebase import initialize_project_firebase

from ..firebase_models.mobile_sales import MobileSalesBillDocument
from ..models import MobileSalesBill


@dataclass
class MobileSalesRecord:
    id: str | int | None
    shop_id: int
    name: str
    lot_no: str
    total_bags: int
    net_weight: float


class MobileSalesRepository:
    def using_firebase(self):
        return settings.FIREBASE_ENABLED and settings.USE_FIREBASE_MOBILE_SALES

    def create(self, *, shop_id, name, lot_no, total_bags, net_weight):
        if self.using_firebase():
            initialize_project_firebase()
            sales_bill = MobileSalesBillDocument(
                shop_id=str(shop_id),
                name=name,
                lot_no=str(lot_no),
                total_bags=int(total_bags),
                net_weight=float(net_weight),
            ).save()
            return self._from_firebase(sales_bill)

        sales_bill = MobileSalesBill.objects.create(
            shop_id=shop_id,
            name=name,
            lot_no=str(lot_no),
            total_bags=int(total_bags),
            net_weight=float(net_weight),
        )
        return self._from_sql(sales_bill)

    def list_by_shop(self, shop_id):
        if self.using_firebase():
            initialize_project_firebase()
            return [
                self._from_firebase(item)
                for item in MobileSalesBillDocument.objects.filter(shop_id=str(shop_id))
            ]

        return [
            self._from_sql(item)
            for item in MobileSalesBill.objects.filter(shop_id=shop_id)
        ]

    def list_by_shop_and_customer_name(self, shop_id, customer_name):
        if self.using_firebase():
            initialize_project_firebase()
            return [
                self._from_firebase(item)
                for item in MobileSalesBillDocument.objects.filter(
                    shop_id=str(shop_id),
                    name=customer_name,
                )
            ]

        return [
            self._from_sql(item)
            for item in MobileSalesBill.objects.filter(
                shop_id=shop_id,
                name=customer_name,
            )
        ]

    def delete_by_shop_and_customer_name(self, shop_id, customer_name):
        if self.using_firebase():
            initialize_project_firebase()
            deleted = 0
            for item in MobileSalesBillDocument.objects.filter(
                shop_id=str(shop_id),
                name=customer_name,
            ):
                item.delete()
                deleted += 1
            return deleted

        deleted, _ = MobileSalesBill.objects.filter(
            shop_id=shop_id,
            name=customer_name,
        ).delete()
        return deleted

    @staticmethod
    def _from_sql(item):
        return MobileSalesRecord(
            id=item.id,
            shop_id=item.shop_id,
            name=item.name,
            lot_no=str(item.lot_no),
            total_bags=int(item.total_bags),
            net_weight=float(item.net_weight),
        )

    @staticmethod
    def _from_firebase(item):
        return MobileSalesRecord(
            id=item.id,
            shop_id=int(item.shop_id),
            name=item.name,
            lot_no=str(item.lot_no),
            total_bags=int(item.total_bags),
            net_weight=float(item.net_weight),
        )