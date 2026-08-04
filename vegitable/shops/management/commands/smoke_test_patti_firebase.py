import json
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError
from django.test.client import RequestFactory

from ...repositories.arrival_repository import ArrivalGoodsRecord, ArrivalRepository
from ...repositories.patti_repository import PattiRepository
from ...repositories.sales_bill_repository import SalesBillItemRecord, SalesBillRepository
from ...shop_views.patti_view import get_all_farmer_name, get_sales_list_for_arrival_item_list


class Command(BaseCommand):
    help = 'Validate Firestore-backed patti read/write paths for unsettled farmer lookup and patti settlement.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--shop-id',
            type=int,
            default=999996,
            help='Temporary shop_id to use for the Firebase patti smoke test.',
        )

    def handle(self, *args, **options):
        arrival_repository = ArrivalRepository()
        patti_repository = PattiRepository()
        sales_repository = SalesBillRepository()

        if not arrival_repository.using_firebase() or not sales_repository.using_firebase() or not patti_repository.using_firebase():
            raise CommandError(
                'Set FIREBASE_ENABLED=True, USE_FIREBASE_ARRIVAL=True, USE_FIREBASE_SALES=True, and USE_FIREBASE_PATTI=True before running this command.'
            )

        token = uuid4().hex[:8]
        shop_id = options['shop_id']
        request_factory = RequestFactory()
        fake_user = SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            is_anonymous=False,
            id=1,
            pk=1,
        )
        fake_shop = SimpleNamespace(pk=shop_id)

        arrival_record = None
        sales_record = None
        patti_record = None

        try:
            arrival_record = arrival_repository.create(
                shop_id=shop_id,
                arrival_id=f'ARR-PATTI-{token}',
                gp_no=f'GP-PATTI-{token}',
                lorry_no=f'LORRY-P-{token[:5]}',
                date='2026-08-04',
                patti_name=f'patti-smoke-{token[:4]}',
                total_bags=10,
                empty_data=False,
                goods=[
                    ArrivalGoodsRecord(
                        local_id='patti-goods-1',
                        former_name='Farmer Patti',
                        item_name='Tomato',
                        initial_qty=10,
                        qty=10,
                        weight=100.0,
                        remarks='Lot P1',
                        advance=5.0,
                        patti_status=False,
                    )
                ],
            )

            sales_record = sales_repository.create(
                shop_id=shop_id,
                sales_bill_id=f'SB-PATTI-{token}',
                payment_type='cash',
                customer_name=f'customer-patti-{token[:4]}',
                date='2026-08-04',
                rmc=1.0,
                commission=1.0,
                cooli=1.0,
                total_amount=40.0,
                paid_amount=40.0,
                balance_amount=0.0,
                empty_data=False,
                items=[
                    SalesBillItemRecord(
                        arrival_entry_id=str(arrival_record.id),
                        arrival_goods_local_id='patti-goods-1',
                        item_name='Tomato',
                        bags=4,
                        net_weight=40.0,
                        rates=10.0,
                        amount=40.0,
                    )
                ],
            )

            unsettled_entries = arrival_repository.list_unsettled_entries(shop_id)
            if not any(str(entry.id) == str(arrival_record.id) for entry in unsettled_entries):
                raise CommandError('Arrival record should appear in unsettled patti entries before settlement.')

            with patch('shops.shop_views.patti_view.Shop.objects.get', return_value=fake_shop):
                farmer_request = request_factory.get('/get_all_farmer_name', {'lorry_number': str(arrival_record.id)})
                farmer_request.user = fake_user  # type: ignore[assignment]
                farmer_response = get_all_farmer_name(farmer_request)
                farmer_payload = _to_payload(farmer_response)
                farmer_list = farmer_payload.get('farmer_list', [])
                if 'Farmer Patti' not in farmer_list:
                    raise CommandError('Firestore patti farmer lookup did not return expected unsettled farmer name.')

                sales_request = request_factory.get(
                    '/get_sales_list_for_arrival_item_list',
                    {
                        'patti_lorry': str(arrival_record.id),
                        'patti_farmer': 'Farmer Patti',
                    },
                )
                sales_request.user = fake_user  # type: ignore[assignment]
                sales_response = get_sales_list_for_arrival_item_list(sales_request)
                sales_payload = _to_payload(sales_response)
                rows = sales_payload.get('sales_goods_list', [])
                if not rows:
                    raise CommandError('Firestore patti sales list did not return any rows for the test data.')
                if round(float(rows[0].get('sold_qty', 0)), 2) != 4.0:
                    raise CommandError('Firestore patti sales list returned unexpected sold_qty for test data.')

            settled_count = arrival_repository.mark_goods_settled(
                shop_id=shop_id,
                entry_id=arrival_record.id,
                former_name='Farmer Patti',
            )
            if settled_count <= 0:
                raise CommandError('Firestore patti settlement did not mark any goods as settled.')

            remaining_names = arrival_repository.list_unsettled_farmer_names(shop_id, arrival_record.id)
            if remaining_names:
                raise CommandError('Firestore patti settlement left unexpected unsettled farmer names.')

            patti_record = patti_repository.create(
                shop_id=shop_id,
                patti_id=f'PT-{token}',
                lorry_no=arrival_record.lorry_no,
                date='2026-08-04',
                advance=5.0,
                farmer_name='Farmer Patti',
                total_weight=40.0,
                hamali=2.0,
                net_amount=33.0,
                items=[
                    {
                        'item': 'Tomato',
                        'lot_no': 'Lot P1',
                        'weight': '40.0',
                        'rate': '10.0',
                        'amount': 40.0,
                    }
                ],
            )

            fetched_patti = patti_repository.get_by_id(patti_record.id)
            if fetched_patti is None:
                raise CommandError('Firestore patti record could not be fetched by id.')
            if len(fetched_patti.items) != 1:
                raise CommandError('Firestore patti record did not persist expected item rows.')

            patti_record = patti_repository.update(
                record_id=patti_record.id,
                shop_id=shop_id,
                patti_id=f'PT-{token}',
                lorry_no=arrival_record.lorry_no,
                date='2026-08-04',
                advance=5.0,
                farmer_name='Farmer Patti',
                total_weight=50.0,
                hamali=3.0,
                net_amount=47.0,
                items=[
                    {
                        'item': 'Tomato',
                        'lot_no': 'Lot P1',
                        'weight': '50.0',
                        'rate': '10.0',
                        'amount': 50.0,
                    }
                ],
            )

            updated_patti = patti_repository.get_by_id(patti_record.id)
            if updated_patti is None:
                raise CommandError('Updated Firestore patti record could not be fetched by id.')
            if round(float(updated_patti.total_weight), 2) != 50.0:
                raise CommandError('Firestore patti update did not persist total_weight changes.')
            if len(updated_patti.items) != 1 or updated_patti.items[0].weight != '50.0':
                raise CommandError('Firestore patti update did not persist updated item rows.')

            patti_list = patti_repository.list_by_shop(shop_id)
            if not any(str(item.id) == str(patti_record.id) for item in patti_list):
                raise CommandError('Firestore patti list_by_shop did not include created test record.')

            self.stdout.write(self.style.SUCCESS('Firebase patti smoke test passed.'))
            self.stdout.write(f'Validated patti Firestore read/write paths for shop_id={shop_id}.')

        except Exception:
            if patti_record is not None:
                try:
                    patti_repository.delete(patti_record.id)
                except Exception:
                    pass
            if sales_record is not None:
                try:
                    sales_repository.delete(sales_record.id, restore_stock=True)
                except Exception:
                    pass
            if arrival_record is not None:
                try:
                    arrival_repository.delete(arrival_record.id)
                except Exception:
                    pass
            raise

        if patti_record is not None:
            patti_repository.delete(patti_record.id)
        if sales_record is not None:
            sales_repository.delete(sales_record.id, restore_stock=True)
        if arrival_record is not None:
            arrival_repository.delete(arrival_record.id)


def _to_payload(response):
    if hasattr(response, 'data'):
        return response.data
    if hasattr(response, 'render'):
        response.render()
    return json.loads(response.content)
