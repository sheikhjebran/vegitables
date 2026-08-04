from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError

from ...repositories.arrival_repository import ArrivalGoodsRecord, ArrivalRepository
from ...repositories.credit_bill_repository import CreditBillRepository
from ...repositories.expenditure_repository import ExpenditureRepository
from ...repositories.patti_repository import PattiRepository
from ...repositories.sales_bill_repository import SalesBillItemRecord, SalesBillRepository
from ...shop_views.shilk_view import get_sales_bag_count_detail_for_selected_date


class Command(BaseCommand):
    help = 'Validate Firestore-backed Shilk patti totals with temporary Firestore sales, credit, and patti data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--shop-id',
            type=int,
            default=None,
            help='Temporary shop_id to use for the Firebase Shilk patti smoke test. If omitted, a unique ID is generated per run.',
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

        arrival_record = None
        sales_cash = None
        sales_credit = None
        credit_record = None
        patti_record = None

        try:
            arrival_record = arrival_repository.create(
                shop_id=shop_id,
                arrival_id=f'ARR-SHILK-{token}',
                gp_no=f'GP-SHILK-{token}',
                lorry_no=f'LORRY-S-{token[:5]}',
                date=today,
                patti_name=f'patti-shilk-{token[:4]}',
                total_bags=10,
                empty_data=False,
                goods=[
                    ArrivalGoodsRecord(
                        local_id='shilk-patti-goods-1',
                        former_name='Farmer Shilk',
                        item_name='Tomato',
                        initial_qty=10,
                        qty=10,
                        weight=100.0,
                        remarks='Lot SP1',
                        advance=0.0,
                        patti_status=False,
                    )
                ],
            )

            sales_cash = sales_repository.create(
                shop_id=shop_id,
                sales_bill_id=f'SBS-C-{token}',
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
                        arrival_goods_local_id='shilk-patti-goods-1',
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
                sales_bill_id=f'SBS-R-{token}',
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
                        arrival_goods_local_id='shilk-patti-goods-1',
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

            patti_record = patti_repository.create(
                shop_id=shop_id,
                patti_id=f'PT-SHILK-{token}',
                lorry_no=arrival_record.lorry_no,
                date=today,
                advance=0.0,
                farmer_name='Farmer Shilk',
                total_weight=20.0,
                hamali=0.0,
                net_amount=11.0,
                items=[
                    {
                        'item': 'Tomato',
                        'lot_no': 'Lot SP1',
                        'weight': '20.0',
                        'rate': '5.5',
                        'amount': 11.0,
                    }
                ],
            )

            shilk_data = get_sales_bag_count_detail_for_selected_date(selected_date=today, shop_id=shop_id)
            if round(float(shilk_data.get('patti_amount', 0.0)), 2) != 11.0:
                raise CommandError('Shilk payload did not return expected Firestore patti amount.')
            if round(float(shilk_data.get('total_sales', 0.0)), 2) != 80.0:
                raise CommandError('Shilk payload returned unexpected total_sales for test data.')
            if round(float(shilk_data.get('collection', 0.0)), 2) != 5.0:
                raise CommandError('Shilk payload returned unexpected collection for test data.')
            if round(float(shilk_data.get('net_amount', 0.0)), 2) != 54.0:
                raise CommandError('Shilk payload returned unexpected net_amount after Firestore patti inclusion.')

            self.stdout.write(self.style.SUCCESS('Firebase Shilk patti smoke test passed.'))
            self.stdout.write(f'Validated Shilk Firestore patti totals for shop_id={shop_id}.')

        except Exception:
            if patti_record is not None:
                try:
                    patti_repository.delete(patti_record.id)
                except Exception:
                    pass
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

        if patti_record is not None:
            patti_repository.delete(patti_record.id)
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
