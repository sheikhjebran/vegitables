from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError

from ...repositories.arrival_repository import ArrivalGoodsRecord, ArrivalRepository
from ...repositories.sales_bill_repository import SalesBillItemRecord, SalesBillRepository


class Command(BaseCommand):
    help = 'Write, read, update, stock-reconcile, restore, and delete a temporary Firestore sales bill record.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--shop-id',
            type=int,
            default=None,
            help='Temporary shop_id to use for the Firebase smoke test. If omitted, a unique ID is generated per run.',
        )

    def handle(self, *args, **options):
        arrival_repository = ArrivalRepository()
        sales_repository = SalesBillRepository()
        if not sales_repository.using_firebase():
            raise CommandError(
                'Set FIREBASE_ENABLED=True, USE_FIREBASE_ARRIVAL=True, and USE_FIREBASE_SALES=True before running this command.'
            )

        token = uuid4().hex[:12]
        shop_id = options['shop_id'] if options['shop_id'] is not None else _generated_shop_id(token)
        arrival_record = None
        sales_record = None
        try:
            arrival_record = arrival_repository.create(
                shop_id=shop_id,
                arrival_id=f'ARR-SALES-{token}',
                gp_no=f'GP-SALES-{token}',
                lorry_no=f'LORRY-SALES-{token[:6]}',
                date='2026-08-04',
                patti_name=f'patti-sales-{token[:5]}',
                total_bags=10,
                empty_data=False,
                goods=[
                    ArrivalGoodsRecord(
                        local_id='sales-goods-1',
                        former_name='Farmer Sales',
                        item_name='Tomato',
                        initial_qty=10,
                        qty=10,
                        weight=100.0,
                        remarks='Lot S1',
                        advance=0.0,
                        patti_status=False,
                    )
                ],
            )

            sales_record = sales_repository.create(
                shop_id=shop_id,
                sales_bill_id=f'SB-{token}',
                payment_type='cash',
                customer_name=f'customer-{token[:6]}',
                date='2026-08-04',
                rmc=1.0,
                commission=2.0,
                cooli=3.0,
                total_amount=50.0,
                paid_amount=50.0,
                balance_amount=0.0,
                empty_data=False,
                items=[
                    SalesBillItemRecord(
                        arrival_entry_id=str(arrival_record.id),
                        arrival_goods_local_id='sales-goods-1',
                        item_name='Tomato',
                        bags=3,
                        net_weight=30.0,
                        rates=10.0,
                        amount=30.0,
                    )
                ],
            )

            fetched_sales = sales_repository.get_by_id(sales_record.id)
            if fetched_sales is None or len(fetched_sales.items) != 1:
                raise CommandError('Created Firestore sales bill could not be fetched correctly.')

            _, updated_goods = arrival_repository.get_goods_by_local_id_any_status(shop_id, 'sales-goods-1')
            if updated_goods is None or updated_goods.qty != 7:
                raise CommandError('Arrival stock was not decremented correctly by the Firestore sales bill create path.')

            sales_record = sales_repository.update(
                record_id=sales_record.id,
                shop_id=shop_id,
                sales_bill_id=f'SB-{token}',
                payment_type='cash',
                customer_name=f'customer-{token[:6]}',
                date='2026-08-04',
                rmc=1.0,
                commission=2.0,
                cooli=3.0,
                total_amount=60.0,
                paid_amount=60.0,
                balance_amount=0.0,
                empty_data=False,
                items=[
                    SalesBillItemRecord(
                        arrival_entry_id=str(arrival_record.id),
                        arrival_goods_local_id='sales-goods-1',
                        item_name='Tomato',
                        bags=5,
                        net_weight=50.0,
                        rates=10.0,
                        amount=50.0,
                    )
                ],
            )

            _, post_update_goods = arrival_repository.get_goods_by_local_id_any_status(shop_id, 'sales-goods-1')
            if post_update_goods is None or post_update_goods.qty != 5:
                raise CommandError('Arrival stock was not reconciled correctly after Firestore sales bill update.')

            sales_record = sales_repository.update(
                record_id=sales_record.id,
                shop_id=shop_id,
                sales_bill_id=f'SB-{token}',
                payment_type='cash',
                customer_name=f'customer-{token[:6]}',
                date='2026-08-04',
                rmc=1.0,
                commission=2.0,
                cooli=3.0,
                total_amount=20.0,
                paid_amount=20.0,
                balance_amount=0.0,
                empty_data=False,
                items=[
                    SalesBillItemRecord(
                        arrival_entry_id=str(arrival_record.id),
                        arrival_goods_local_id='sales-goods-1',
                        item_name='Tomato',
                        bags=1,
                        net_weight=10.0,
                        rates=10.0,
                        amount=10.0,
                    )
                ],
            )

            _, post_second_update_goods = arrival_repository.get_goods_by_local_id_any_status(shop_id, 'sales-goods-1')
            if post_second_update_goods is None or post_second_update_goods.qty != 9:
                raise CommandError('Arrival stock was not restored correctly when reducing Firestore sales bill bags.')

            deleted = sales_repository.delete(sales_record.id, restore_stock=True)
            if not deleted:
                raise CommandError('Expected the temporary Firestore sales bill record to be deleted.')

            _, restored_goods = arrival_repository.get_goods_by_local_id_any_status(shop_id, 'sales-goods-1')
            if restored_goods is None or restored_goods.qty != 10:
                raise CommandError('Arrival stock was not restored correctly when deleting the Firestore sales bill.')

            self.stdout.write(self.style.SUCCESS('Firebase SalesBill smoke test passed.'))
            self.stdout.write(f'Created temporary sales record id={sales_record.id} for shop_id={shop_id}.')
        except KeyboardInterrupt as error:
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
            raise CommandError(
                'Sales bill Firebase smoke test was interrupted while waiting on Firestore. '
                'Retry the command; if the issue persists, check Firestore connectivity and gRPC stability.'
            ) from error
        except Exception:
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
        else:
            if arrival_record is not None:
                arrival_repository.delete(arrival_record.id)


def _generated_shop_id(token):
    # Keep generated IDs in a high range to avoid clashing with real shops.
    return 900000 + (int(token[:6], 16) % 90000)