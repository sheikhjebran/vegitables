from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from ..models import Shop, CreditBillEntry, ExpenditureEntry, CreditBillHistory, PattiEntry, SalesBillEntry, \
    ArrivalGoods, ArrivalEntry
from django.db.models import Sum, F, Q
from django.db import models
from rest_framework import status

from ..utility import getDate_from_string


def shilk_entry(request):
    if request.user.is_authenticated:
        return render(request, 'Report/shilk.html')
    return render(request, 'index.html')


@api_view(['GET'])
def retrieve_shilk(request):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        response = get_sales_bag_count_detail_for_selected_date(
            selected_date=request.GET['selected_date'],
            shop_id=shop_detail_object
        )
        return JsonResponse(data={'FOUND': True, 'result': response}, status=status.HTTP_200_OK)
    return JsonResponse(data={'FOUND': False}, status=status.HTTP_404_NOT_FOUND)


def get_sales_bag_count_detail_for_selected_date(selected_date: str, shop_id):
    selected_date = getDate_from_string(selected_date)

    # Aggregate total bags
    arrival_entries = ArrivalEntry.objects.filter(
        date=selected_date,
        shop=shop_id
    )
    total_bags_sum = arrival_entries.aggregate(
        total_bags_sum=models.Sum('total_bags'))['total_bags_sum'] or 0

    # Aggregate balance bags
    goods = ArrivalGoods.objects.filter(arrival_entry__in=arrival_entries)
    balance_bags_sum = goods.aggregate(balance_bags_sum=models.Sum('qty'))[
        'balance_bags_sum'] or 0

    # Calculate bags sold
    bags_sold_sum = total_bags_sum - balance_bags_sum

    # Aggregate sales data
    sales_data = SalesBillEntry.objects.filter(
        shop=shop_id,
        date=selected_date,
    ).aggregate(
        cash_bill_amount=Sum('paid_amount', filter=Q(payment_type='cash')),
        upi_amount=Sum('paid_amount', filter=Q(payment_type='upi')),
        credit_bill_amount=Sum(
            'balance_amount', filter=Q(payment_type='credit')),
        total_sales=Sum('total_amount')
    )

    patti_entries = PattiEntry.objects.filter(
        date=selected_date,
        shop=shop_id
    ).aggregate(
        net_amount=Sum('net_amount')
    )['net_amount'] or 0

    collection = CreditBillHistory.objects.filter(
        credit_bill__shop_id=shop_id,
        date=selected_date
    ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0

    total_expenditure = ExpenditureEntry.objects.filter(
        shop=shop_id,
        date=selected_date
    ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0

    # Fetching the initial credit bill amount for the specific date
    initial_credit_bill_amount = CreditBillEntry.objects.filter(
        shop=shop_id,
        sales_bill__date=selected_date  # Joining with SalesBillEntry
    ).aggregate(
        total_initial_credit=Sum('initial_credit_bill_amount')
    ).get('total_initial_credit') or 0

    # Set default values to zero if None
    cash_bill_amount = sales_data.get('cash_bill_amount') or 0
    # sales_data.get('credit_bill_amount') or 0
    credit_bill_amount = initial_credit_bill_amount
    total_sales = sales_data.get('total_sales') or 0
    upi_amount = sales_data.get('upi_amount') or 0
    patti = round(patti_entries, 2)

    cash_balance = cash_bill_amount + collection - total_expenditure

    net_amount = (total_sales + collection) - \
        (credit_bill_amount + upi_amount + patti + total_expenditure)

    return {
        'total_bags_sum': total_bags_sum,
        'bags_sold_sum': bags_sold_sum,
        'balance_bags_sum': balance_bags_sum,
        'cash_bill_amount': cash_bill_amount,
        'total_sales': total_sales,
        'credit_bill_amount': credit_bill_amount,
        'collection': collection,
        'upi_amount': upi_amount,
        'total_expenditure': total_expenditure,
        'net_amount': round(net_amount, 2),
        'patti_amount': patti,
        'cash_balance': cash_balance
    }
