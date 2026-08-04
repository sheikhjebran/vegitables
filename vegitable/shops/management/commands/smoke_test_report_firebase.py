from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError

from ...repositories.arrival_repository import ArrivalGoodsRecord, ArrivalRepository
from ...repositories.credit_bill_repository import CreditBillRepository
from ...repositories.sales_bill_repository import SalesBillItemRecord, SalesBillRepository
from ...shop_views.rmc_view import build_daily_rmc_data, build_weekly_rmc_data
from ...shop_views.shilk_view import get_sales_bag_count_detail_for_selected_date


class Command(BaseCommand):
    help = 'Validate Firestore-backed RMC and Shilk report payload builders with temporary test data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--shop-id',
            type=int,
            default=999998,
            help='Temporary shop_id to use for the Firebase report smoke test.',
        )

    def handle(self, *args, **options):
        arrival_repository = ArrivalRepository()
        sales_repository = SalesBillRepository()
        credit_repository = CreditBillRepository()

        if not arrival_repository.using_firebase() or not sales_repository.using_firebase() or not credit_repository.using_firebase():
            raise CommandError(
                'Set FIREBASE_ENABLED=True, USE_FIREBASE_ARRIVAL=True, USE_FIREBASE_SALES=True, and USE_FIREBASE_CREDIT=True before running this command.'
            )

        token = uuid4().hex[:8]
        today = '2026-08-04'
        shop_id = options['shop_id']

        arrival_record = None
        sales_cash = None
        sales_credit = None
        credit_record = None

        try:
            arrival_record = arrival_repository.create(
                shop_id=shop_id,
                arrival_id=f'ARR-REPORT-{token}',
                gp_no=f'GP-REPORT-{token}',
                lorry_no=f'LORRY-R-{token[:6]}',
                date=today,
                patti_name=f'patti-report-{token[:4]}',
                total_bags=10,
                empty_data=False,
                goods=[
                    ArrivalGoodsRecord(
                        local_id='report-goods-1',
                        former_name='Farmer Report',
                        item_name='Tomato',
                        initial_qty=10,
                        qty=10,
                        weight=100.0,
                        remarks='Lot R1',
                        advance=0.0,
                        patti_status=False,
                    )
                ],
            )

            sales_cash = sales_repository.create(
                shop_id=shop_id,
                sales_bill_id=f'SBR-C-{token}',
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
                        arrival_goods_local_id='report-goods-1',
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
                sales_bill_id=f'SBR-R-{token}',
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
                        arrival_goods_local_id='report-goods-1',
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

            daily_rows = build_daily_rmc_data(shop_id, today)
            if len(daily_rows) < 2:
                raise CommandError('RMC daily payload builder did not return expected bill rows for Firestore test data.')

            weekly_rows = build_weekly_rmc_data(shop_id, today, today)
            if len(weekly_rows) != 1:
                raise CommandError('RMC weekly payload builder did not return exactly one aggregated row for a single test date.')
            if round(float(weekly_rows[0].get('Total_Amount', 0.0)), 2) != 80.0:
                raise CommandError('RMC weekly payload builder returned unexpected total amount for Firestore test data.')

            shilk_data = get_sales_bag_count_detail_for_selected_date(selected_date=today, shop_id=shop_id)
            if round(float(shilk_data.get('total_sales', 0.0)), 2) != 80.0:
                raise CommandError('Shilk payload builder returned unexpected total_sales for Firestore test data.')
            if round(float(shilk_data.get('credit_bill_amount', 0.0)), 2) != 20.0:
                raise CommandError('Shilk payload builder returned unexpected credit_bill_amount for Firestore test data.')
            if round(float(shilk_data.get('collection', 0.0)), 2) != 5.0:
                raise CommandError('Shilk payload builder returned unexpected collection for Firestore test data.')

            self.stdout.write(self.style.SUCCESS('Firebase report smoke test passed.'))
            self.stdout.write(f'Validated RMC/Shilk Firestore payload builders for shop_id={shop_id}.')

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
