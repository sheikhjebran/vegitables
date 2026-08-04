from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError
from django.test.client import RequestFactory

from ...repositories.arrival_repository import ArrivalGoodsRecord, ArrivalRepository
from ...repositories.sales_bill_repository import SalesBillItemRecord, SalesBillRepository
from ...shop_views.rmc_view import print_rmc_daily_report, print_rmc_weekly_report


class Command(BaseCommand):
    help = 'Validate Firestore-backed RMC PDF report endpoints (daily and weekly) with temporary Firestore data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--shop-id',
            type=int,
            default=999996,
            help='Temporary shop_id to use for the Firebase report PDF smoke test.',
        )

    def handle(self, *args, **options):
        arrival_repository = ArrivalRepository()
        sales_repository = SalesBillRepository()

        if not arrival_repository.using_firebase() or not sales_repository.using_firebase():
            raise CommandError(
                'Set FIREBASE_ENABLED=True, USE_FIREBASE_ARRIVAL=True, and USE_FIREBASE_SALES=True before running this command.'
            )

        token = uuid4().hex[:8]
        today = '2026-08-04'
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
        sales_cash = None
        sales_credit = None

        try:
            arrival_record = arrival_repository.create(
                shop_id=shop_id,
                arrival_id=f'ARR-PDF-{token}',
                gp_no=f'GP-PDF-{token}',
                lorry_no=f'LORRY-P-{token[:6]}',
                date=today,
                patti_name=f'patti-pdf-{token[:4]}',
                total_bags=10,
                empty_data=False,
                goods=[
                    ArrivalGoodsRecord(
                        local_id='report-pdf-goods-1',
                        former_name='Farmer Report PDF',
                        item_name='Tomato',
                        initial_qty=10,
                        qty=10,
                        weight=100.0,
                        remarks='Lot RP1',
                        advance=0.0,
                        patti_status=False,
                    )
                ],
            )

            sales_cash = sales_repository.create(
                shop_id=shop_id,
                sales_bill_id=f'SBRP-C-{token}',
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
                        arrival_goods_local_id='report-pdf-goods-1',
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
                sales_bill_id=f'SBRP-R-{token}',
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
                        arrival_goods_local_id='report-pdf-goods-1',
                        item_name='Tomato',
                        bags=2,
                        net_weight=20.0,
                        rates=10.0,
                        amount=20.0,
                    )
                ],
            )

            with patch('shops.shop_views.rmc_view.Shop.objects.get', return_value=fake_shop):
                daily_request = request_factory.get('/print_rmc_daily_report', {'date': today})
                daily_request.user = fake_user
                daily_response = print_rmc_daily_report(daily_request)
                self._validate_pdf_response(daily_response, 'daily')

                weekly_request = request_factory.get('/print_rmc_weekly_report', {'start_date': today, 'end_date': today})
                weekly_request.user = fake_user
                weekly_response = print_rmc_weekly_report(weekly_request)
                self._validate_pdf_response(weekly_response, 'weekly')

            self.stdout.write(self.style.SUCCESS('Firebase report PDF smoke test passed.'))
            self.stdout.write(f'Validated RMC daily/weekly Firestore PDF endpoints for shop_id={shop_id}.')

        except Exception:
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

        if sales_credit is not None:
            sales_repository.delete(sales_credit.id, restore_stock=True)
        if sales_cash is not None:
            sales_repository.delete(sales_cash.id, restore_stock=True)
        if arrival_record is not None:
            arrival_repository.delete(arrival_record.id)

    def _validate_pdf_response(self, response, label):
        if getattr(response, 'status_code', 500) != 200:
            raise CommandError(f'RMC {label} PDF endpoint returned non-200 status: {getattr(response, "status_code", "unknown")}.')
        content_type = response.get('Content-Type', '')
        if 'application/pdf' not in content_type:
            raise CommandError(f'RMC {label} PDF endpoint did not return PDF content type: {content_type}')
        if len(response.content or b'') == 0:
            raise CommandError(f'RMC {label} PDF endpoint returned an empty PDF response.')
