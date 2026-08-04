from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError

from ...repositories.arrival_repository import ArrivalGoodsRecord, ArrivalRepository


class Command(BaseCommand):
    help = 'Write, read, update, duplicate-check, goods-list, and delete a temporary ArrivalEntry record through the Firestore-backed repository.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--shop-id',
            type=int,
            default=999999,
            help='Temporary shop_id to use for the Firebase smoke test.',
        )

    def handle(self, *args, **options):
        repository = ArrivalRepository()
        if not repository.using_firebase():
            raise CommandError(
                'Set FIREBASE_ENABLED=True and USE_FIREBASE_ARRIVAL=True before running this command.'
            )

        token = uuid4().hex[:12]
        shop_id = options['shop_id']
        created_record = None
        try:
            created_record = repository.create(
                shop_id=shop_id,
                arrival_id=f'ARR-{token}',
                gp_no=f'GP-{token}',
                lorry_no=f'LORRY-{token[:6]}',
                date='2026-08-04',
                patti_name=f'patti-{token[:5]}',
                total_bags=10,
                empty_data=False,
                goods=[
                    ArrivalGoodsRecord(
                        local_id='goods-1',
                        former_name='Farmer One',
                        item_name='Tomato',
                        initial_qty=10,
                        qty=10,
                        weight=120.5,
                        remarks='Fresh',
                        advance=25.0,
                        patti_status=False,
                    ),
                    ArrivalGoodsRecord(
                        local_id='goods-2',
                        former_name='Farmer Two',
                        item_name='Onion',
                        initial_qty=5,
                        qty=0,
                        weight=55.0,
                        remarks='Sold out',
                        advance=10.0,
                        patti_status=True,
                    ),
                ],
            )

            fetched_record = repository.get_by_id(created_record.id)
            if fetched_record is None or len(fetched_record.goods) != 2:
                raise CommandError('Created Firestore arrival record could not be fetched correctly.')

            duplicates = repository.find_duplicate(
                shop_id=shop_id,
                lorry_no=created_record.lorry_no,
                date=created_record.date,
            )
            if not any(str(record.id) == str(created_record.id) for record in duplicates):
                raise CommandError('Created Firestore arrival record was not found via duplicate check.')

            available_goods = repository.list_available_goods_by_shop(shop_id)
            if not any(str(entry.id) == str(created_record.id) and goods.item_name == 'Tomato' for entry, goods in available_goods):
                raise CommandError('Available goods list did not expose the expected Firestore arrival goods row.')

            repository.update(
                record_id=created_record.id,
                shop_id=shop_id,
                arrival_id=created_record.arrival_id,
                gp_no=created_record.gp_no,
                lorry_no=created_record.lorry_no,
                date=created_record.date,
                patti_name=created_record.patti_name,
                total_bags=12,
                empty_data=False,
                goods=[
                    ArrivalGoodsRecord(
                        local_id='goods-1',
                        former_name='Farmer One',
                        item_name='Tomato',
                        initial_qty=10,
                        qty=8,
                        weight=120.5,
                        remarks='Updated',
                        advance=25.0,
                        patti_status=False,
                    )
                ],
            )

            updated_record = repository.get_by_id(created_record.id)
            if updated_record is None or updated_record.total_bags != 12 or len(updated_record.goods) != 1:
                raise CommandError('Updated Firestore arrival record does not reflect the new values.')

            deleted = repository.delete(created_record.id)
            if not deleted:
                raise CommandError('Expected the temporary Firestore arrival record to be deleted.')

            if repository.get_by_id(created_record.id) is not None:
                raise CommandError('Temporary Firestore arrival record still exists after delete.')

            self.stdout.write(self.style.SUCCESS('Firebase Arrival smoke test passed.'))
            self.stdout.write(f'Created temporary record id={created_record.id} for shop_id={shop_id}.')
        except Exception:
            if created_record is not None:
                try:
                    repository.delete(created_record.id)
                except Exception:
                    pass
            raise