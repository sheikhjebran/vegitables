from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from ..repositories.credit_bill_repository import CreditBillRepository
from ..repositories.sales_bill_repository import SalesBillRepository
from ..repositories.shop_metadata_repository import ShopMetadataRepository
from ..utility import get_float_number
import datetime
from rest_framework import status


credit_bill_repository = CreditBillRepository()
sales_bill_repository = SalesBillRepository()
shop_metadata_repository = ShopMetadataRepository()


def _credit_workflow_requires_firebase():
    return sales_bill_repository.using_firebase() and credit_bill_repository.using_firebase()


def _credit_firebase_required_message():
    return 'Enable USE_FIREBASE_SALES=True and USE_FIREBASE_CREDIT=True. SQL credit path has been removed.'


def _load_shop_metadata(user_id):
    return shop_metadata_repository.require_by_owner_user_id(user_id)


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

        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'success': False, 'message': str(error)}, status=400)

        if not _credit_workflow_requires_firebase():
            return JsonResponse({
                'success': False,
                'message': _credit_firebase_required_message(),
            }, status=400)

        search_name_lower = search_name.lower()
        result = []
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

            result.append({
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
            request, 'Entry/CreditBill/partial_table_rows.html', {'results': result}).content.decode()
        return JsonResponse({'success': True, 'html': rendered_table_rows})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def add_new_credit_bill_entry(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=401)

    try:
        shop_detail_object = _load_shop_metadata(request.user.id)
    except ValueError as error:
        return JsonResponse({'success': False, 'message': str(error)}, status=400)

    balance_amount = get_float_number(
        request.POST['credit_bill_balance_amount'])
    sales_bill_id = request.POST['credit_bill_sales_bill_id']
    payment_mode = request.POST['credit_bill_payment_option']
    amount_received = get_float_number(
        request.POST['credit_bill_amount_received'])
    bill_discount = get_float_number(request.POST['credit_bill_discount'])

    amount = round(amount_received + bill_discount, 2)

    if not _credit_workflow_requires_firebase():
        return JsonResponse(
            {
                'success': False,
                'message': _credit_firebase_required_message(),
            },
            status=400,
        )

    sales_record = sales_bill_repository.get_by_id(sales_bill_id)
    if sales_record is None:
        return JsonResponse({'success': False, 'message': 'Sales bill not found.'}, status=404)
    if int(sales_record.shop_id) != int(shop_detail_object.pk):
        return JsonResponse({'success': False, 'message': 'Sales bill does not belong to your shop.'}, status=403)

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


@api_view(('GET',))
@renderer_classes((JSONRenderer,))
def get_credit_bill_entry_list(request):
    if not request.user.is_authenticated:
        return Response(data={'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    if not _credit_workflow_requires_firebase():
        return Response(
            data={
                'error': _credit_firebase_required_message(),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        shop_detail_object = _load_shop_metadata(request.user.id)
    except ValueError as error:
        return Response(data={'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)

    credit_record = credit_bill_repository.get_by_id(request.GET['id'])
    if credit_record is None:
        return Response(data={'error': 'Credit bill not found.'}, status=status.HTTP_404_NOT_FOUND)
    if int(credit_record.shop_id) != int(shop_detail_object.pk):
        return Response(data={'error': 'Credit bill does not belong to your shop.'}, status=status.HTTP_403_FORBIDDEN)

    history_list = credit_record.histories
    data = []
    for single_credit in history_list:
        data.append({
            'date': single_credit.date,
            'amount': single_credit.amount,
            'payment_mode': single_credit.payment_mode,
        })
    return Response(data=data, status=status.HTTP_200_OK)
