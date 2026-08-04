import json
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError
from django.test.client import RequestFactory

from ...repositories.arrival_repository import ArrivalGoodsRecord, ArrivalRepository
from ...repositories.credit_bill_repository import CreditBillRepository
from ...repositories.expenditure_repository import ExpenditureRepository
from ...repositories.patti_repository import PattiRepository
from ...repositories.sales_bill_repository import SalesBillItemRecord, SalesBillRepository
from ...shop_views.rmc_view import get_daily_rmc_selected_date, get_daily_rmc_start_and_end_date
from ...shop_views.shilk_view import retrieve_shilk


class Command(BaseCommand):
    help = 'Validate Firestore-backed RMC/Shilk HTTP endpoint payloads with temporary Firestore data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--shop-id',
            type=int,
            default=None,
            help='Temporary shop_id to use for the Firebase report HTTP smoke test. If omitted, a unique ID is generated per run.',
        )

    def handle(self, *args, **options):
        arrival_repository = ArrivalRepository()
        sales_repository = SalesBillRepository()
        credit_repository = CreditBillRepository()
        patti_repository = PattiRepository()
        expenditure_repository = ExpenditureRepository()

        if (
            not arrival_repository.using_firebase()
            or not sales_repository.using_firebase()
            or not credit_repository.using_firebase()
            or not patti_repository.using_firebase()
            or not expenditure_repository.using_firebase()
        ):
            raise CommandError(
                'Set FIREBASE_ENABLED=True, USE_FIREBASE_ARRIVAL=True, USE_FIREBASE_SALES=True, USE_FIREBASE_CREDIT=True, USE_FIREBASE_PATTI=True, and USE_FIREBASE_EXPENDITURE=True before running this command.'
            )

        token = uuid4().hex[:8]
        today = '2026-08-04'
        shop_id = options['shop_id'] if options['shop_id'] is not None else _generated_shop_id(token)
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
        sales_cash = None
        sales_credit = None
        credit_record = None

        try:
            arrival_record = arrival_repository.create(
                shop_id=shop_id,
                arrival_id=f'ARR-HTTP-{token}',
                gp_no=f'GP-HTTP-{token}',
                lorry_no=f'LORRY-H-{token[:6]}',
                date=today,
                patti_name=f'patti-http-{token[:4]}',
                total_bags=10,
                empty_data=False,
                goods=[
                    ArrivalGoodsRecord(
                        local_id='report-http-goods-1',
                        former_name='Farmer Report HTTP',
                        item_name='Tomato',
                        initial_qty=10,
                        qty=10,
                        weight=100.0,
                        remarks='Lot RH1',
                        advance=0.0,
                        patti_status=False,
                    )
                ],
            )

            sales_cash = sales_repository.create(
                shop_id=shop_id,
                sales_bill_id=f'SBRH-C-{token}',
                payment_type='cash',
                customer_name=f'customer-cash-{token[:4]}',
                date=today,
                rmc=1.0,
                commission=1.0,
                cooli=1.0,
                total_amount=30.0,
                paid_amount=30.0,
                balance_amount=0.0,
                empty_data=False,
                items=[
                    SalesBillItemRecord(
                        arrival_entry_id=str(arrival_record.id),
                        arrival_goods_local_id='report-http-goods-1',
                        item_name='Tomato',
                        bags=3,
                        net_weight=30.0,
                        rates=10.0,
                        amount=30.0,
                    )
                ],
            )

            sales_credit = sales_repository.create(
                shop_id=shop_id,
                sales_bill_id=f'SBRH-R-{token}',
                payment_type='credit',
                customer_name=f'customer-credit-{token[:4]}',
                date=today,
                rmc=2.0,
                commission=2.0,
                cooli=2.0,
                total_amount=50.0,
                paid_amount=30.0,
                balance_amount=20.0,
                empty_data=False,
                items=[
                    SalesBillItemRecord(
                        arrival_entry_id=str(arrival_record.id),
                        arrival_goods_local_id='report-http-goods-1',
                        item_name='Tomato',
                        bags=2,
                        net_weight=20.0,
                        rates=10.0,
                        amount=20.0,
                    )
                ],
            )

            credit_record = credit_repository.upsert_for_sales_bill(
                shop_id=shop_id,
                customer_name=sales_credit.customer_name,
                sales_bill_record_id=sales_credit.id,
                sales_bill_id=sales_credit.sales_bill_id,
                initial_credit_bill_amount=sales_credit.balance_amount,
            )
            credit_repository.add_payment(
                credit_bill_record_id=credit_record.id,
                amount=5.0,
                payment_mode='CASH',
                date=today,
            )

            with patch('shops.shop_views.rmc_view.Shop.objects.get', return_value=fake_shop), patch(
                'shops.shop_views.shilk_view.Shop.objects.get', return_value=fake_shop
            ):
                daily_request = request_factory.get('/get_daily_rmc_selected_date', {'date': today})
                daily_request.user = fake_user
                daily_response = get_daily_rmc_selected_date(daily_request)
                daily_payload = _to_payload(daily_response)
                if not daily_payload.get('FOUND'):
                    raise CommandError('RMC daily endpoint did not return FOUND=True with Firestore test data.')
                if len(daily_payload.get('result', [])) < 2:
                    raise CommandError('RMC daily endpoint did not return expected bill rows for Firestore test data.')

                weekly_request = request_factory.get('/get_daily_rmc_start_and_end_date', {'start_date': today, 'end_date': today})
                weekly_request.user = fake_user
                weekly_response = get_daily_rmc_start_and_end_date(weekly_request)
                weekly_payload = _to_payload(weekly_response)
                if not weekly_payload.get('FOUND'):
                    raise CommandError('RMC weekly endpoint did not return FOUND=True with Firestore test data.')
                weekly_rows = weekly_payload.get('result', [])
                if len(weekly_rows) != 1:
                    raise CommandError('RMC weekly endpoint did not return exactly one aggregated row for a single test date.')
                if round(float(weekly_rows[0].get('Total_Amount', 0.0)), 2) != 80.0:
                    raise CommandError('RMC weekly endpoint returned unexpected total amount for Firestore test data.')

                shilk_request = request_factory.get('/retrieve_shilk', {'selected_date': today})
                shilk_request.user = fake_user
                shilk_response = retrieve_shilk(shilk_request)
                shilk_payload = _to_payload(shilk_response)
                if not shilk_payload.get('FOUND'):
                    raise CommandError('Shilk endpoint did not return FOUND=True with Firestore test data.')
                shilk_data = shilk_payload.get('result', {})
                if round(float(shilk_data.get('total_sales', 0.0)), 2) != 80.0:
                    raise CommandError('Shilk endpoint returned unexpected total_sales for Firestore test data.')
                if round(float(shilk_data.get('credit_bill_amount', 0.0)), 2) != 20.0:
                    raise CommandError('Shilk endpoint returned unexpected credit_bill_amount for Firestore test data.')
                if round(float(shilk_data.get('collection', 0.0)), 2) != 5.0:
                    raise CommandError('Shilk endpoint returned unexpected collection for Firestore test data.')

            self.stdout.write(self.style.SUCCESS('Firebase report HTTP smoke test passed.'))
            self.stdout.write(f'Validated RMC/Shilk Firestore HTTP payloads for shop_id={shop_id}.')

        except Exception:
            if credit_record is not None:
                try:
                    credit_repository.delete(credit_record.id)
                except Exception:
                    pass
            if sales_credit is not None:
                try:
                    sales_repository.delete(sales_credit.id, restore_stock=True)
                except Exception:
                    pass
            if sales_cash is not None:
                try:
                    sales_repository.delete(sales_cash.id, restore_stock=True)
                except Exception:
                    pass
            if arrival_record is not None:
                try:
                    arrival_repository.delete(arrival_record.id)
                except Exception:
                    pass
            raise

        if credit_record is not None:
            credit_repository.delete(credit_record.id)
        if sales_credit is not None:
            sales_repository.delete(sales_credit.id, restore_stock=True)
        if sales_cash is not None:
            sales_repository.delete(sales_cash.id, restore_stock=True)
        if arrival_record is not None:
            arrival_repository.delete(arrival_record.id)


def _generated_shop_id(token):
    # Keep generated IDs in a high range to avoid clashing with real shops.
    return 900000 + (int(token[:6], 16) % 90000)


def _to_payload(response):
    if hasattr(response, 'render'):
        response.render()
    if hasattr(response, 'data'):
        return response.data
    return json.loads(response.content)
