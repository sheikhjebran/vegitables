from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from rest_framework import response, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from ..models import Shop
from datetime import date
import re
from django.shortcuts import render
from django.core.paginator import Paginator
from ..utility import generate_unique_number
from ..repositories.arrival_repository import ArrivalRepository
from ..repositories.credit_bill_repository import CreditBillRepository
from ..repositories.mobile_sales_repository import MobileSalesRepository
from ..repositories.shop_metadata_repository import ShopMetadataRepository
from ..repositories.sales_bill_repository import SalesBillItemRecord, SalesBillRepository


mobile_sales_repository = MobileSalesRepository()
arrival_repository = ArrivalRepository()
sales_bill_repository = SalesBillRepository()
credit_bill_repository = CreditBillRepository()
shop_metadata_repository = ShopMetadataRepository()


def _sales_firebase_enabled():
    return sales_bill_repository.using_firebase()


def _sales_firebase_required_message():
    return 'Enable USE_FIREBASE_SALES=True. SQL sales path has been removed.'


def _arrival_firebase_enabled():
    return arrival_repository.using_firebase()


def _arrival_firebase_required_message():
    return 'Enable USE_FIREBASE_ARRIVAL=True for Firebase-only sales workflows.'


def _load_shop_metadata(user_id):
    return shop_metadata_repository.require_by_owner_user_id(user_id)


def sales_bill_entry(request, current_page=1):
    if request.user.is_authenticated:
        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            messages.error(request, str(error))
            return render(request, 'index.html')

        if not _sales_firebase_enabled():
            messages.error(request, _sales_firebase_required_message())
            empty_page = Paginator([], 10).get_page(1)
            return render(request, 'Entry/Sales/sales_bill_entry.html', {
                'shop_details': shop_detail_object,
                'sales_bill_detail': empty_page,
                'current_page': current_page,
                'use_firebase_sales': False,
            })

        try:
            sales_entry_detail = sales_bill_repository.list_by_shop(shop_detail_object.pk)
            items_per_page = 10
            paginator = Paginator(sales_entry_detail, items_per_page)
            sales_entry_detail = paginator.get_page(current_page)

        except Exception as error:
            print(error)
            sales_entry_detail = Paginator([], 10).get_page(1)

        return render(request, 'Entry/Sales/sales_bill_entry.html', {
            'shop_details': shop_detail_object,
            'sales_bill_detail': sales_entry_detail,
            'current_page': current_page,
            'use_firebase_sales': True,
        })

    return render(request, 'index.html')


def sales_bill_next_page(request, page_number):
    return sales_bill_entry(request, current_page=page_number + 1)


def sales_bill_prev_page(request, page_number):
    if page_number > 1:
        return sales_bill_entry(request, current_page=page_number - 1)
    else:
        return sales_bill_entry(request)


def navigate_to_add_sales_bill_entry(request):
    if request.user.is_authenticated:
        today = date.today()
        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            messages.error(request, str(error))
            return render(request, 'index.html')

        if not _sales_firebase_enabled():
            messages.error(request, _sales_firebase_required_message())
            return sales_bill_entry(request)

        if not _arrival_firebase_enabled():
            messages.error(request, _arrival_firebase_required_message())
            return sales_bill_entry(request)

        arrival_detail_object = [goods for _, goods in arrival_repository.list_available_goods_by_shop(shop_detail_object.pk)]
        sales_bill_index = {
            'sales_entry_prefix': shop_detail_object.sales_bill_entry_prefix,
            'sales_entry_counter': int(shop_detail_object.sales_bill_entry_counter) + 1
        }

        mobile_sales_customer = mobile_sales_repository.list_by_shop(shop_detail_object.pk)

        customer_list = []
        for customer in mobile_sales_customer:
            if customer.name not in customer_list:
                customer_list.append(customer.name)
        request.session['form_token'] = generate_unique_number()
        return render(request, 'Entry/Sales/modify_sales_bill_entry.html', {
            'sales_bill_detail': True,
            'new': True,
            "arrival_goods_detail": arrival_detail_object,
            "today": today,
            "sales_bill_index": sales_bill_index,
            "customer_list": customer_list,
            'use_firebase_sales': True,
        })
    return render(request, 'index.html')


def modify_sales_bill_entry(request):
    if request.user.is_authenticated:
        if request.POST.get('form_token') == str(request.session.get('form_token')):
            # Remove the token from the session
            del request.session['form_token']
            try:
                shop_detail_object = _load_shop_metadata(request.user.id)
            except ValueError as error:
                messages.error(request, str(error))
                request.session['form_token'] = generate_unique_number()
                return render(request, 'index.html')

            if not _sales_firebase_enabled():
                messages.error(request, _sales_firebase_required_message())
                request.session['form_token'] = generate_unique_number()
                return sales_bill_entry(request)

            if not _arrival_firebase_enabled():
                messages.error(request, _arrival_firebase_required_message())
                request.session['form_token'] = generate_unique_number()
                return sales_bill_entry(request)

            is_new = str(request.POST['new']) == "True"

            balance_amount = round(float(request.POST['balance_amount']), 2)
            if balance_amount > 0.0 and not credit_bill_repository.using_firebase():
                messages.error(
                    request,
                    'Enable USE_FIREBASE_CREDIT=True when using Firestore sales with outstanding balances.',
                )
                request.session['form_token'] = generate_unique_number()
                return sales_bill_entry(request)

            mobile_sales_repository.delete_by_shop_and_customer_name(
                shop_detail_object.pk,
                request.POST['sales_entry_customer_name'],
            )

            sales_items = build_firestore_sales_items(request, list(request.POST), shop_detail_object.pk)
            if is_new:
                sales_record = sales_bill_repository.create(
                    shop_id=shop_detail_object.pk,
                    sales_bill_id=request.POST['sales_bill_id'],
                    payment_type=request.POST['payment_mode'],
                    customer_name=request.POST['sales_entry_customer_name'],
                    date=request.POST['sales_entry_date'],
                    rmc=request.POST['rmc'],
                    commission=request.POST['comission'],
                    cooli=request.POST['cooli'],
                    total_amount=round(float(request.POST['total_amount']), 2),
                    paid_amount=round(float(request.POST['paid_amount']), 2),
                    balance_amount=balance_amount,
                    empty_data=False,
                    items=sales_items,
                )
                shop_metadata_repository.increment_counter(request.user.id, 'sales_bill_entry_counter')
            else:
                sales_record_id = request.POST.get('id')
                if not sales_record_id:
                    messages.error(request, 'Sales bill id is required for Firestore update.')
                    request.session['form_token'] = generate_unique_number()
                    return sales_bill_entry(request)

                sales_record = sales_bill_repository.update(
                    record_id=sales_record_id,
                    shop_id=shop_detail_object.pk,
                    sales_bill_id=request.POST['sales_bill_id'],
                    payment_type=request.POST['payment_mode'],
                    customer_name=request.POST['sales_entry_customer_name'],
                    date=request.POST['sales_entry_date'],
                    rmc=request.POST['rmc'],
                    commission=request.POST['comission'],
                    cooli=request.POST['cooli'],
                    total_amount=round(float(request.POST['total_amount']), 2),
                    paid_amount=round(float(request.POST['paid_amount']), 2),
                    balance_amount=balance_amount,
                    empty_data=False,
                    items=sales_items,
                )

            sync_firestore_credit_bill(
                sales_record=sales_record,
                shop_id=shop_detail_object.pk,
            )
        request.session['form_token'] = generate_unique_number()
        return sales_bill_entry(request)
    return render(request, 'index.html')


def build_firestore_sales_items(request, request_list, shop_id):
    lot_number_list = []
    bags_list = []
    net_weight_list = []
    rates_list = []
    amount_list = []
    item_name_list = []

    for item in request_list:
        if re.search("^.*_lot_number$", item):
            lot_number_list.append(item)
        if re.search("^.*_item_name$", item):
            item_name_list.append(item)
        if re.search("^.*_bags$", item):
            bags_list.append(item)
        if re.search("^.*_net_weight$", item):
            net_weight_list.append(item)
        if re.search("^.*_rates$", item):
            rates_list.append(item)
        if re.search("^.*_amount$", item):
            amount_list.append(item)

    sales_items = []
    for index in range(0, len(lot_number_list)):
        local_id = request.POST[lot_number_list[index]]
        arrival_entry, arrival_goods = arrival_repository.get_goods_by_local_id_any_status(shop_id, local_id)
        if arrival_entry is None or arrival_goods is None:
            raise ValueError(f'Arrival goods {local_id} was not found in Firestore.')
        sales_items.append(SalesBillItemRecord(
            arrival_entry_id=str(arrival_entry.id),
            arrival_goods_local_id=arrival_goods.local_id,
            item_name=request.POST[item_name_list[index]],
            bags=int(request.POST[bags_list[index]]),
            net_weight=float(request.POST[net_weight_list[index]]),
            rates=float(request.POST[rates_list[index]]),
            amount=float(request.POST[amount_list[index]]),
        ))
    return sales_items


def sync_firestore_credit_bill(*, sales_record, shop_id):
    if not credit_bill_repository.using_firebase():
        return
    if float(sales_record.balance_amount) <= 0.0:
        return

    credit_bill_repository.upsert_for_sales_bill(
        shop_id=shop_id,
        customer_name=sales_record.customer_name,
        sales_bill_record_id=sales_record.id,
        sales_bill_id=sales_record.sales_bill_id,
        initial_credit_bill_amount=float(sales_record.balance_amount),
    )


@csrf_protect
def edit_sales_bill_entry(request, sales_id):
    if request.user.is_authenticated:
        if not _sales_firebase_enabled():
            messages.error(request, _sales_firebase_required_message())
            return sales_bill_entry(request)

        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            messages.error(request, str(error))
            return render(request, 'index.html')

        sales_obj = sales_bill_repository.get_by_id(sales_id)
        if sales_obj is None:
            messages.error(request, 'Firestore sales bill not found.')
            return sales_bill_entry(request)

        arrival_goods_detail = list(arrival_repository.list_available_goods_by_shop(shop_detail_object.pk))
        goods_map = {str(goods.local_id): goods for _, goods in arrival_goods_detail}
        for item in sales_obj.items:
            if str(item.arrival_goods_local_id) not in goods_map:
                _, goods = arrival_repository.get_goods_by_local_id_any_status(
                    shop_detail_object.pk,
                    item.arrival_goods_local_id,
                )
                if goods is not None:
                    goods_map[str(goods.local_id)] = goods

        sales_item_objs = []
        for index, item in enumerate(sales_obj.items):
            _, goods = arrival_repository.get_goods_by_local_id_any_status(
                shop_detail_object.pk,
                item.arrival_goods_local_id,
            )
            available_qty = 0 if goods is None else goods.qty
            sales_item_objs.append({
                'row_id': index,
                'arrival_goods_local_id': item.arrival_goods_local_id,
                'item_name': item.item_name,
                'bags': item.bags,
                'net_weight': item.net_weight,
                'rates': item.rates,
                'amount': item.amount,
                'available_qty': available_qty,
            })

        request.session['form_token'] = generate_unique_number()
        return render(request, 'Entry/Sales/modify_sales_bill_entry.html', {
            'sales_bill_detail': False,
            'new': False,
            'use_firebase_sales': True,
            'arrival_goods_detail': sorted(goods_map.values(), key=lambda item: str(item.local_id)),
            'sales_obj': sales_obj,
            'sales_item_objs': sales_item_objs,
        })
    return render(request, 'index.html')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mobile_customer_detail(request):
    try:
        # Fetch shop detail object based on the authenticated user
        shop_detail_object = _load_shop_metadata(request.user.id)
        selected_customer = request.GET.get('selectedCustomer', '').strip()

        if not _arrival_firebase_enabled():
            return JsonResponse(
                data={'success': False, 'error': _arrival_firebase_required_message()},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch mobile sales data for the selected customer
        results = mobile_sales_repository.list_by_shop_and_customer_name(
            shop_detail_object.pk,
            selected_customer,
        )

        response = []
        for single_result in results:
            _, arrival_goods = arrival_repository.get_goods_by_local_id(
                shop_detail_object.pk,
                single_result.lot_no,
            )
            arrival_data = []
            if arrival_goods is not None:
                arrival_data.append({
                    'id': arrival_goods.local_id,
                    'shop__id': shop_detail_object.pk,
                    'former_name': arrival_goods.former_name,
                    'initial_qty': arrival_goods.initial_qty,
                    'qty': arrival_goods.qty,
                    'weight': arrival_goods.weight,
                    'remarks': arrival_goods.remarks,
                    'item_name': arrival_goods.item_name,
                    'advance': arrival_goods.advance,
                    'patti_status': arrival_goods.patti_status,
                })
            for data in arrival_data:
                data["net_weight"] = single_result.net_weight
                data["total_bags"] = single_result.total_bags
            response.append(arrival_data)

        if response:
            return JsonResponse(data={'success': True, 'data': response}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(data={'success': False}, status=status.HTTP_404_NOT_FOUND)

    except Shop.DoesNotExist:
        return JsonResponse(data={'success': False, 'error': 'Shop not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return JsonResponse(data={'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
