from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from ..models import Shop, CreditBillEntry, CreditBillHistory, SalesBillEntry
from ..utility import get_float_number, getDate_from_string
import datetime
from rest_framework import status


def credit_bill_entry(request):
    if request.user.is_authenticated:
        return render(request, 'Entry/CreditBill/credit_bill.html')
    return render(request, 'index.html')


def search_credit(request):
    if request.user.is_authenticated:
        # Get name, default to an empty string
        search_name = request.GET.get('name', '').strip()
        # Get date, default to None
        search_date = request.GET.get('date', None)

        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        query = CreditBillEntry.objects.filter(shop_id=shop_detail_object)

        if search_name:
            # Filter by name if provided
            query = query.filter(customer_name__icontains=search_name)

        if search_date:
            # Filter by date if provided
            query = query.filter(date=search_date)

        # Execute the query
        credit_obj = query

        result = []
        for credit in credit_obj:
            balance_amount = credit.sales_bill.balance_amount
            if balance_amount > 0:  # Check if the balance is greater than zero
                myDict = {
                    "id": credit.id,
                    "customer_name": credit.customer_name,
                    "date": credit.sales_bill.date,
                    "bill_no": credit.sales_bill.id,
                    "amount": credit.sales_bill.total_amount,
                    "paid": credit.sales_bill.paid_amount,
                    "balance": balance_amount
                }
                result.append(myDict)
        rendered_table_rows = render(
            request, 'Entry/CreditBill/partial_table_rows.html', {'results': result}).content.decode()
        return JsonResponse({'success': True, 'html': rendered_table_rows})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def add_new_credit_bill_entry(request):
    balance_amount = get_float_number(
        request.POST['credit_bill_balance_amount'])
    sales_bill_id = request.POST['credit_bill_sales_bill_id']
    payment_mode = request.POST['credit_bill_payment_option']
    amount_received = get_float_number(
        request.POST['credit_bill_amount_received'])
    bill_discount = get_float_number(request.POST['credit_bill_discount'])

    amount = round(amount_received + bill_discount, 2)
    balance_amount -= amount
    sales_bill = SalesBillEntry.objects.get(id=sales_bill_id)
    sales_bill.paid_amount = round(sales_bill.paid_amount + amount, 2)
    sales_bill.balance_amount = round(balance_amount, 2)
    sales_bill.save()

    credit_bill = CreditBillEntry.objects.get(sales_bill=sales_bill_id)

    creditBillHistory = CreditBillHistory(
        amount=round(float(amount), 2),
        payment_mode=payment_mode,
        credit_bill=credit_bill,
        date=datetime.datetime.today()
    )
    creditBillHistory.save()

    mutable_get = request.GET.copy()
    mutable_get['name'] = credit_bill.customer_name
    request.GET = mutable_get

    return search_credit(request)


@api_view(('GET',))
@renderer_classes((JSONRenderer,))
def get_credit_bill_entry_list(request):
    [...]

    credit_bill_entry_object = CreditBillEntry.objects.get(
        id=request.GET['id'])
    credit_bill_history_list = CreditBillHistory.objects.filter(
        credit_bill=credit_bill_entry_object).order_by('-id')

    data = []
    for single_credit in credit_bill_history_list:
        credit = {
            'date': single_credit.date,
            'amount': single_credit.amount,
            'payment_mode': single_credit.payment_mode
        }
        data.append(credit)
    return Response(data=data, status=status.HTTP_200_OK)
