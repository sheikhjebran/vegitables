from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from rest_framework import response, status
from rest_framework.decorators import api_view

from ..models import Shop, SalesBillEntry, SalesBillItem, MobileSalesBill, ArrivalGoods, Index, CreditBillEntry, \
    CreditBillHistory
from datetime import date
import re
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from ..utility import getDate_from_string, generate_unique_number
import datetime
from django.db.models import Sum, F, Q


def sales_bill_entry(request, current_page=1):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        sales_entry_detail = None

        try:
            sales_entry_detail = SalesBillEntry.objects.filter(
                shop=shop_detail_object, Empty_data=False).order_by('-id')

            # Add pagination
            items_per_page = 10
            paginator = Paginator(sales_entry_detail, items_per_page)
            sales_entry_detail = paginator.get_page(current_page)

            for entry in sales_entry_detail:

                total_net_weight = SalesBillItem.objects.filter(Sales_Bill_Entry=entry).aggregate(
                    total_weight=Sum('net_weight')
                )['total_weight']

                entry.total_net_weight = total_net_weight if total_net_weight is not None else 0

        except Exception as error:
            print(error)

        return render(request, 'Entry/Sales/sales_bill_entry.html', {
            'shop_details': shop_detail_object,
            'sales_bill_detail': sales_entry_detail,
            'current_page': current_page
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
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        arrival_detail_object = ArrivalGoods.objects.filter(
            shop=shop_detail_object, qty__gte=1)

        index = get_object_or_404(Index, shop=shop_detail_object)

        sales_bill_index = {
            'sales_entry_prefix': index.sales_bill_entry_prefix,
            'sales_entry_counter': int(index.sales_bill_entry_counter) + 1
        }

        mobile_sales_customer = MobileSalesBill.objects.filter(
            shop=shop_detail_object)

        customer_list = []
        for customer in mobile_sales_customer:
            if customer.name not in customer_list:
                customer_list.append(customer.name)

        return render(request, 'Entry/Sales/modify_sales_bill_entry.html', {
            'sales_bill_detail': True,
            'new': True,
            "arrival_goods_detail": arrival_detail_object,
            "today": today,
            "sales_bill_index": sales_bill_index,
            "customer_list": customer_list
        })
    return render(request, 'index.html')


def modify_sales_bill_entry(request):
    if request.user.is_authenticated:
        if request.POST.get('form_token') == str(request.session.get('form_token')):
            # Remove the token from the session
            del request.session['form_token']
            shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
            if str(request.POST['new']) == "True":
                sales_bill_entry_Obj = SalesBillEntry(
                    sales_bill_id=request.POST['sales_bill_id'],
                    payment_type=request.POST['payment_mode'],
                    customer_name=request.POST['sales_entry_customer_name'],
                    date=getDate_from_string(request.POST['sales_entry_date']),
                    shop=shop_detail_object,
                    rmc=request.POST['rmc'],
                    commission=request.POST['comission'],
                    cooli=request.POST['cooli'],
                    total_amount=round(float(request.POST['total_amount']), 2),
                    paid_amount=round(float(request.POST['paid_amount']), 2),
                    balance_amount=round(
                        float(request.POST['balance_amount']), 2),
                    Empty_data=False
                )

                MobileSalesBill.objects.filter(
                    name=request.POST['sales_entry_customer_name']).delete()

            else:
                sales_bill_entry_Obj = SalesBillEntry.objects.get(
                    id=request.POST['id'])
                sales_bill_entry_Obj.payment_type = request.POST['payment_mode']
                sales_bill_entry_Obj.customer_name = request.POST['sales_entry_customer_name']
                sales_bill_entry_Obj.date = getDate_from_string(
                    request.POST['sales_entry_date'])
                sales_bill_entry_Obj.shop = shop_detail_object
                sales_bill_entry_Obj.rmc = request.POST['rmc']
                sales_bill_entry_Obj.commission = request.POST['comission']
                sales_bill_entry_Obj.cooli = request.POST['cooli']
                sales_bill_entry_Obj.total_amount = round(
                    float(request.POST['total_amount']), 2)
                sales_bill_entry_Obj.paid_amount = round(
                    float(request.POST['paid_amount']), 2)
                sales_bill_entry_Obj.balance_amount = round(
                    float(request.POST['balance_amount']), 2)
                sales_bill_entry_Obj.Empty_data = False

            sales_bill_entry_Obj.save()

            if str(request.POST['new']) == "True":
                index_obj = get_object_or_404(Index, shop=shop_detail_object)

                # Increment the arrival_entry_counter
                index_obj.sales_bill_entry_counter += 1
                index_obj.save()

            print(f"New Sales Bill entry  = {sales_bill_entry_Obj.id}")
            if sales_bill_entry_Obj.balance_amount > 0.0:
                add_to_credit_bill_db(sales_bill_entry_Obj, shop_detail_object, sales_bill_entry_Obj.customer_name,
                                      sales_bill_entry_Obj.balance_amount)
            add_sales_bill_item(request, list(
                request.POST), sales_bill_entry_Obj)
        request.session['form_token'] = generate_unique_number()
        return sales_bill_entry(request)
    return render(request, 'index.html')


def add_sales_bill_item(request, request_list, sales):
    if request.user.is_authenticated:
        lot_number_list = []
        bags_list = []
        net_weight_list = []
        rates_list = []
        amount_list = []
        item_name_list = []

        for i in request_list:

            lot_number_regrex = re.search("^.*_lot_number$", i)
            if lot_number_regrex:
                lot_number_list.append(i)

            item_name_regrex = re.search("^.*_item_name$", i)
            if item_name_regrex:
                item_name_list.append(i)

            bag_regrex = re.search("^.*_bags$", i)
            if bag_regrex:
                bags_list.append(i)

            net_weight_regrex = re.search("^.*_net_weight$", i)
            if net_weight_regrex:
                net_weight_list.append(i)

            rates_regrex = re.search("^.*_rates$", i)
            if rates_regrex:
                rates_list.append(i)

            amount_regrex = re.search("^.*_amount$", i)
            if amount_regrex:
                amount_list.append(i)

        for i in range(0, len(lot_number_list)):
            arrival_goods_entry_Obj = ArrivalGoods.objects.get(
                id=request.POST[lot_number_list[i]])

            arrival_goods_entry_Obj.qty = int(
                arrival_goods_entry_Obj.qty) - int(request.POST[bags_list[i]])
            arrival_goods_entry_Obj.save()

            sales_bill_entry_Obj = SalesBillItem(
                item_name=request.POST[item_name_list[i]],
                arrival_goods=arrival_goods_entry_Obj,
                bags=request.POST[bags_list[i]],
                net_weight=request.POST[net_weight_list[i]],
                rates=request.POST[rates_list[i]],
                amount=request.POST[amount_list[i]],
                Sales_Bill_Entry=sales
            )

            sales_bill_entry_Obj.save()

            print(f"New Sales Bill item  = {sales_bill_entry_Obj.id}")
    return render(request, 'index.html')


def add_to_credit_bill_db(sales, shop, customer_name, balance_amount):
    credit_bill_entry = CreditBillEntry(
        customer_name=customer_name,
        sales_bill=sales,
        shop=shop,
        initial_credit_bill_amount=float(balance_amount)
    )
    credit_bill_entry.save()

    credit_bill_history = CreditBillHistory(
        date=datetime.datetime.today(),
        amount=0.0,
        credit_bill=credit_bill_entry
    )
    credit_bill_history.save()


@csrf_protect
def edit_sales_bill_entry(request, sales_id):
    if request.user.is_authenticated:
        sales_obj = SalesBillEntry.objects.get(pk=sales_id)
        sales_item_objs = SalesBillItem.objects.filter(
            Sales_Bill_Entry=sales_obj).order_by('-id')

        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        selected_arrival_goods_ids = sales_item_objs.values_list(
            'arrival_goods', flat=True)

        arrival_detail_object = ArrivalGoods.objects.filter(
            Q(shop=shop_detail_object) &
            (Q(qty__gte=1) & Q(id__in=selected_arrival_goods_ids))
        )

        for iteam in sales_item_objs:
            print(iteam)

        return render(request, 'Entry/Sales/modify_sales_bill_entry.html',
                      {'sales_bill_detail': False,
                       "arrival_goods_detail": arrival_detail_object,
                       "sales_obj": sales_obj,
                       "sales_item_objs": sales_item_objs
                       }
                      )
    return render(request, 'index.html')


@api_view(['GET'])
def get_mobile_customer_detail(request):
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    selected_customer = request.GET.get('selectedCustomer', '').strip()
    results = MobileSalesBill.objects.filter(name=selected_customer)

    response = []
    for single_result in results:
        arrival_detail_object = ArrivalGoods.objects.filter(
            shop=shop_detail_object).filter(id=single_result.lot_no)
        arrival_data = list(arrival_detail_object.values(
            "id", "shop__id", "former_name", "initial_qty", "qty",
            "weight", "remarks", "item_name", "advance", "patti_status"
        ))
        for data in arrival_data:
            data["net_weight"] = single_result.net_weight
            data["total_bags"] = single_result.total_bags
        response.append(arrival_data)

    if response:
        return JsonResponse(data={'success': True, 'data': response}, status=status.HTTP_200_OK)
    else:
        return JsonResponse(data={'success': False}, status=status.HTTP_404_NOT_FOUND)
