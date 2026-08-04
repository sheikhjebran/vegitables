from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from ..models import Shop, CreditBillEntry, CreditBillHistory, SalesBillEntry
from ..repositories.credit_bill_repository import CreditBillRepository
from ..repositories.sales_bill_repository import SalesBillRepository
from ..utility import get_float_number, getDate_from_string
import datetime
from rest_framework import status


credit_bill_repository = CreditBillRepository()
sales_bill_repository = SalesBillRepository()


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

        if sales_bill_repository.using_firebase() and not credit_bill_repository.using_firebase():
            return JsonResponse({
                'success': False,
                'message': 'Enable USE_FIREBASE_CREDIT=True when USE_FIREBASE_SALES=True for credit workflows.',
            }, status=400)

        if credit_bill_repository.using_firebase():
            search_name_lower = search_name.lower()
            results = []
            for credit in credit_bill_repository.list_by_shop(shop_detail_object.pk):
                if search_name_lower and search_name_lower not in credit.customer_name.lower():
                    continue

                sales_record = sales_bill_repository.get_by_id(credit.sales_bill_record_id)
                if sales_record is None:
                    continue
                if search_date and str(sales_record.date) != str(search_date):
                    continue
                if float(sales_record.balance_amount) <= 0.0:
                    continue

                results.append({
                    'id': credit.id,
                    'customer_name': credit.customer_name,
                    'date': sales_record.date,
                    'bill_no': sales_record.id,
                    'bill_label': sales_record.sales_bill_id,
                    'amount': sales_record.total_amount,
                    'paid': sales_record.paid_amount,
                    'balance': sales_record.balance_amount,
                })

            rendered_table_rows = render(
                request, 'Entry/CreditBill/partial_table_rows.html', {'results': results}
            ).content.decode()
            return JsonResponse({'success': True, 'html': rendered_table_rows})

        query = CreditBillEntry.objects.filter(shop_id=shop_detail_object)

        if search_name:
            # Filter by name if provided
            query = query.filter(customer_name__icontains=search_name)

        if search_date:
            # Filter by date if provided
            query = query.filter(sales_bill__date=search_date)

        # Execute the query
        credit_obj = query

        result = []
        for credit in credit_obj:
            balance_amount = credit.sales_bill.balance_amount
            if balance_amount > 0:  # Check if the balance is greater than zero
                myDict = {
                    "id": credit.pk,
                    "customer_name": credit.customer_name,
                    "date": credit.sales_bill.date,
                    "bill_no": credit.sales_bill.pk,
                    "bill_label": credit.sales_bill.sales_bill_id,
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

    if sales_bill_repository.using_firebase() and not credit_bill_repository.using_firebase():
        return JsonResponse(
            {
                'success': False,
                'message': 'Enable USE_FIREBASE_CREDIT=True when USE_FIREBASE_SALES=True for credit workflows.',
            },
            status=400,
        )

    if credit_bill_repository.using_firebase():
        sales_record = sales_bill_repository.get_by_id(sales_bill_id)
        if sales_record is None:
            return JsonResponse({'success': False, 'message': 'Sales bill not found.'}, status=404)

        remaining_balance = round(float(sales_record.balance_amount) - amount, 2)
        if remaining_balance < 0:
            return JsonResponse({'success': False, 'message': 'Received amount cannot exceed Balance Amount ..!'}, status=400)

        paid_amount = round(float(sales_record.paid_amount) + amount, 2)
        if remaining_balance > 0:
            payment_type = 'credit'
        elif payment_mode.strip().upper() == 'UPI':
            payment_type = 'upi'
        else:
            payment_type = 'cash'

        updated_sales = sales_bill_repository.update(
            record_id=sales_record.id,
            shop_id=sales_record.shop_id,
            sales_bill_id=sales_record.sales_bill_id,
            payment_type=payment_type,
            customer_name=sales_record.customer_name,
            date=sales_record.date,
            rmc=sales_record.rmc,
            commission=sales_record.commission,
            cooli=sales_record.cooli,
            total_amount=sales_record.total_amount,
            paid_amount=paid_amount,
            balance_amount=remaining_balance,
            empty_data=sales_record.empty_data,
            items=sales_record.items,
        )

        credit_record = credit_bill_repository.upsert_for_sales_bill(
            shop_id=sales_record.shop_id,
            customer_name=sales_record.customer_name,
            sales_bill_record_id=sales_record.id,
            sales_bill_id=sales_record.sales_bill_id,
            initial_credit_bill_amount=float(updated_sales.balance_amount + amount),
        )

        credit_bill_repository.add_payment(
            credit_bill_record_id=credit_record.id,
            amount=amount,
            payment_mode=payment_mode,
            date=datetime.date.today().isoformat(),
        )

        mutable_get = request.GET.copy()
        mutable_get['name'] = sales_record.customer_name
        request.GET = mutable_get

        return search_credit(request)

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
    if sales_bill_repository.using_firebase() and not credit_bill_repository.using_firebase():
        return Response(
            data={
                'error': 'Enable USE_FIREBASE_CREDIT=True when USE_FIREBASE_SALES=True for credit workflows.',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if credit_bill_repository.using_firebase():
        history_list = credit_bill_repository.list_history(request.GET['id'])
        data = []
        for single_credit in history_list:
            data.append({
                'date': single_credit.date,
                'amount': single_credit.amount,
                'payment_mode': single_credit.payment_mode,
            })
        return Response(data=data, status=status.HTTP_200_OK)

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
