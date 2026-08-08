from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from ..repositories.arrival_repository import ArrivalRepository
from ..repositories.credit_bill_repository import CreditBillRepository
from ..repositories.expenditure_repository import ExpenditureRepository
from ..repositories.patti_repository import PattiRepository
from ..repositories.sales_bill_repository import SalesBillRepository
from ..repositories.shop_metadata_repository import ShopMetadataRepository
from rest_framework import status

from ..utility import getDate_from_string


arrival_repository = ArrivalRepository()
sales_bill_repository = SalesBillRepository()
credit_bill_repository = CreditBillRepository()
expenditure_repository = ExpenditureRepository()
patti_repository = PattiRepository()
shop_metadata_repository = ShopMetadataRepository()


def _shop_pk(shop_or_id):
    return int(getattr(shop_or_id, 'pk', shop_or_id))


def _iso_date(value):
    if isinstance(value, str):
        return value
    return value.isoformat()


def shilk_report(request):
    if request.user.is_authenticated:
        return render(request, 'Report/shilk.html')
    return render(request, 'index.html')


def _load_shop_metadata(user_id):
    return shop_metadata_repository.require_by_owner_user_id(user_id)


@api_view(['GET'])
def retrieve_shilk(request):
    if request.user.is_authenticated:
        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse(
                data={'FOUND': False, 'error': str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            response = get_sales_bag_count_detail_for_selected_date(
                selected_date=request.GET['selected_date'],
                shop_id=shop_detail_object
            )
        except ValueError as error:
            return JsonResponse(
                data={'FOUND': False, 'error': str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return JsonResponse(data={'FOUND': True, 'result': response}, status=status.HTTP_200_OK)
    return JsonResponse(data={'FOUND': False}, status=status.HTTP_404_NOT_FOUND)


def get_sales_bag_count_detail_for_selected_date(selected_date: str, shop_id):
    selected_date = getDate_from_string(selected_date)
    selected_date_iso = _iso_date(selected_date)
    shop_pk = _shop_pk(shop_id)

    if not sales_bill_repository.using_firebase():
        raise ValueError(
            'Enable USE_FIREBASE_SALES=True for shilk report workflows.'
        )

    if not arrival_repository.using_firebase():
        raise ValueError(
            'Enable USE_FIREBASE_ARRIVAL=True when USE_FIREBASE_SALES=True for shilk report workflows.'
        )

    arrival_entries = [
        record for record in arrival_repository.list_by_shop(shop_pk)
        if str(record.date) == selected_date_iso
    ]
    total_bags_sum = sum(int(entry.total_bags) for entry in arrival_entries)
    balance_bags_sum = sum(
        int(goods.qty)
        for entry in arrival_entries
        for goods in entry.goods
    )
    bags_sold_sum = total_bags_sum - balance_bags_sum

    sales_records = [
        record for record in sales_bill_repository.list_by_shop(shop_pk)
        if str(record.date) == selected_date_iso
    ]
    cash_bill_amount = sum(
        float(record.paid_amount)
        for record in sales_records
        if str(record.payment_type).lower() == 'cash'
    )
    upi_amount = sum(
        float(record.paid_amount)
        for record in sales_records
        if str(record.payment_type).lower() == 'upi'
    )
    total_sales = sum(float(record.total_amount) for record in sales_records)

    if not credit_bill_repository.using_firebase():
        raise ValueError(
            'Enable USE_FIREBASE_CREDIT=True when USE_FIREBASE_SALES=True for shilk report workflows.'
        )

    credit_bill_amount = 0.0
    collection = 0.0
    sales_by_id = {str(record.id): record for record in sales_records}
    for credit in credit_bill_repository.list_by_shop(shop_pk):
        sales_record = sales_by_id.get(str(credit.sales_bill_record_id))
        if sales_record is not None:
            credit_bill_amount += float(credit.initial_credit_bill_amount)
        for payment in credit.histories:
            if str(payment.date) == selected_date_iso:
                collection += float(payment.amount)

    if not patti_repository.using_firebase():
        raise ValueError(
            'Enable USE_FIREBASE_PATTI=True when USE_FIREBASE_SALES=True for shilk report workflows.'
        )

    patti_entries = sum(
        float(record.net_amount)
        for record in patti_repository.list_by_shop(shop_pk)
        if str(record.date) == selected_date_iso
    )

    if not expenditure_repository.using_firebase():
        raise ValueError(
            'Enable USE_FIREBASE_EXPENDITURE=True when USE_FIREBASE_SALES=True for shilk report workflows.'
        )

    total_expenditure = expenditure_repository.sum_amount_by_shop_and_date(
        shop_pk,
        selected_date_iso,
    )

    patti = round(patti_entries, 2)
    cash_balance = cash_bill_amount + collection - total_expenditure
    net_amount = (total_sales + collection) - \
        (credit_bill_amount + upi_amount + patti + total_expenditure)

    return {
        'total_bags_sum': total_bags_sum,
        'bags_sold_sum': bags_sold_sum,
        'balance_bags_sum': balance_bags_sum,
        'cash_bill_amount': round(cash_bill_amount, 2),
        'total_sales': round(total_sales, 2),
        'credit_bill_amount': round(credit_bill_amount, 2),
        'collection': round(collection, 2),
        'upi_amount': round(upi_amount, 2),
        'total_expenditure': total_expenditure,
        'net_amount': round(net_amount, 2),
        'patti_amount': patti,
        'cash_balance': round(cash_balance, 2)
    }
