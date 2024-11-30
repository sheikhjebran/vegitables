from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages, auth
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from datetime import date
import re
from django.db import models
from django.core.paginator import Paginator
from . import utility
from .models import ExpenditureEntry, PattiEntry, PattiEntryList, SalesBillEntry, SalesBillItem, Shop, \
    ArrivalEntry, \
    ArrivalGoods, CustomerLedger, FarmerLedger, CreditBillEntry, CreditBillHistory, Index
import datetime
from .report.report import Report
from .utility import consolidate_result_for_report, get_float_number, getDate_from_string
from django.db.models import Sum, F, Q


def index(request):
    return render(request, 'index.html')


def customer_ledger_next_page(request, page_number):
    return customer_ledger(request, current_page=page_number + 1)


def customer_ledger_prev_page(request, page_number):
    if page_number > 1:
        return customer_ledger(request, current_page=page_number - 1)
    else:
        return customer_ledger(request)


def inventory_next_page(request, page_number):
    return inventory(request, current_page=page_number + 1)


def inventory_prev_page(request, page_number):
    if page_number > 1:
        return inventory(request, current_page=page_number - 1)
    else:
        return inventory(request)


def sales_bill_next_page(request, page_number):
    return sales_bill_entry(request, current_page=page_number + 1)


def sales_bill_prev_page(request, page_number):
    if page_number > 1:
        return sales_bill_entry(request, current_page=page_number - 1)
    else:
        return sales_bill_entry(request)


@csrf_protect
def customer_ledger(request, current_page=1, customer_ledger_entry=None):
    if request.user.is_authenticated:
        if customer_ledger_entry is None:
            customer_ledger_entry = {
                "name": "",
                "contact": "",
                "address": "",
                "id": None
            }
        items_per_page = 10
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        request.session['form_token'] = utility.generate_unique_number()
        customer_ledger_list = CustomerLedger.objects.filter(
            shop=shop_detail_object).order_by('-id')
        paginator = Paginator(customer_ledger_list, items_per_page)
        customer_ledger_list = paginator.get_page(current_page)
        return render(request, 'Ledger/customer_ledger.html',
                      {'customer_ledger_list': customer_ledger_list,
                       'current_page': current_page,
                       'customer_ledger': customer_ledger_entry})
    return render(request, 'index.html')


def inventory(request, current_page=1):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

        entries = ArrivalGoods.objects.filter(shop_id=shop_detail_object).values(
            'id',
            'arrival_entry__date',
            'remarks',
            'item_name',
            'initial_qty',
            'qty',
        ).annotate(
            sold=F('initial_qty') - F('qty'),
            balance=F('qty')
        ).filter(qty__gt=0)

        items_per_page = 10
        paginator = Paginator(entries, items_per_page)
        entries = paginator.get_page(current_page)
        return render(request, 'Inventory/inventory.html', {'entries_list': entries,
                                                            'current_page': current_page})
    return render(request, 'index.html')


@csrf_protect
def add_customer_ledger(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            if request.POST.get('form_token') == str(request.session.get('form_token')):
                # Remove the token from the session
                del request.session['form_token']
                if request.POST['customer_ledger_id'] == "None":
                    customer_ledger_obj = CustomerLedger(
                        name=request.POST['name'],
                        contact=request.POST['contact'],
                        address=request.POST['address'],
                        shop=Shop.objects.get(shop_owner=request.user.id)
                    )
                else:
                    customer_ledger_obj = CustomerLedger.objects.get(
                        id=request.POST['customer_ledger_id'])
                    customer_ledger_obj.name = request.POST['name']
                    customer_ledger_obj.contact = request.POST['contact']
                    customer_ledger_obj.address = request.POST['address']
                    customer_ledger_obj.shop = Shop.objects.get(
                        shop_owner=request.user.id)
                customer_ledger_obj.save()
        request.session['form_token'] = utility.generate_unique_number()
        return customer_ledger(request)

    return render(request, 'index.html')


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


def profile(request):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

        profile_data = {
            "username": request.user.username,
            "email": request.user.email,
            "firstname": request.user.first_name,
            "lastname": request.user.last_name,
        }

        return render(request, 'Profile/profile.html',
                      {
                          'shop_details': shop_detail_object,
                          "profile": profile_data
                      })
    else:
        return render(request, 'index.html')


def logout(request):
    auth.logout(request)
    return render(request, 'index.html')


def add_new_expenditure_entry(request):
    if request.user.is_authenticated:
        return render(request, 'modify_expenditure_entry.html', {'expenditure_detail': "NEW"})
    return render(request, 'index.html')


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

        return render(request, 'Entry/Sales/modify_sales_bill_entry.html', {
            'sales_bill_detail': True,
            'new': True,
            "arrival_goods_detail": arrival_detail_object,
            "today": today,
            "sales_bill_index": sales_bill_index
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
        request.session['form_token'] = utility.generate_unique_number()
        return sales_bill_entry(request)
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


def total_amount_expenditure_entry(request):
    if request.user.is_authenticated:
        return render(request, 'expenditure_total_iframe.html')
    return render(request, 'index.html')


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_arrival_goods_item_name(request):
    [...]
    item_name_list = {}
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    arrival_detail_object = ArrivalGoods.objects.filter(
        shop=shop_detail_object).filter(id=request.GET['selected_lot'])

    for arrival_entry in arrival_detail_object:
        item_name_list[arrival_entry.item_name] = arrival_entry.qty

    data = {'item_name_list': item_name_list}
    return Response(data, status=status.HTTP_200_OK)


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_arrival_goods_api(request):
    [...]
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    arrival_goods_obj = ArrivalGoods.objects.filter(
        shop=shop_detail_object, qty__gte=1)

    mylist = {}
    for item in arrival_goods_obj:
        mylist[item.id] = item.qty

    return JsonResponse(mylist, status=status.HTTP_200_OK)


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_arrival_duplicate_validation_api(request):
    [...]
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    respones = ArrivalEntry.objects.filter(shop=shop_detail_object).filter(lorry_no=request.GET['lorry_no']).filter(
        date=request.GET['date'])

    if respones.count() <= 0:
        return JsonResponse(data={'NOT_FOUND': True}, status=status.HTTP_200_OK)
    else:
        return JsonResponse(data={'NOT_FOUND': False}, status=status.HTTP_404_NOT_FOUND)


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_arrival_goods_list(request):
    [...]
    item_goods_list = {}
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    arrival_detail_object = ArrivalGoods.objects.filter(
        shop=shop_detail_object, qty__gte=1)

    for arrival_entry in arrival_detail_object:
        item_goods_list[arrival_entry.id] = arrival_entry.remarks

    data = {'item_goods_list': item_goods_list}
    return Response(data, status=status.HTTP_200_OK)


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_lorry_number_for_date(request, lorry_date):
    [...]
    lorry_number_list = []
    lorry_date = getDate_from_string(lorry_date)
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

    arrival_detail_object = ArrivalEntry.objects.filter(
        shop=shop_detail_object)
    for arrival_entry in arrival_detail_object:
        if arrival_entry.date == lorry_date and arrival_entry.Empty_data is False:
            lorry_number_list.append(arrival_entry.lorry_no)

    data = {'lorry_number_list': lorry_number_list}
    return Response(data, status=status.HTTP_200_OK)


@api_view(('GET',))
def get_daily_rmc_selected_date(request):
    [...]
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    try:
        rmc_date = getDate_from_string(request.GET['date'])
        # Perform the query
        queryset = SalesBillEntry.objects.filter(shop=shop_detail_object, date=rmc_date).annotate(
            total_bags=Sum('salesbillitem__bags'),
            total_paid_amount=F('paid_amount'),
            total_rmc=F('rmc')
        ).values('id', 'payment_type', 'total_bags', 'total_paid_amount', 'total_rmc')

        # Iterate through the results
        data = []
        for entry in queryset:
            single_entry = {
                'entry_id': entry['id'],
                'payment_type': entry['payment_type'],
                'bags': entry['total_bags'],
                'paid_amount': entry['total_paid_amount'],
                'rmc': entry['total_rmc']}
            data.append(single_entry)

        if len(data) > 0:
            return JsonResponse(data={'FOUND': True, 'result': data}, status=status.HTTP_200_OK)
        return JsonResponse(data={'FOUND': False, 'result': data}, status=status.HTTP_200_OK)
    except Exception as error:
        return JsonResponse(data={'FOUND': False, 'result': error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(('GET',))
def get_daily_rmc_start_and_end_date(request):
    [...]
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    try:
        start_date = getDate_from_string(request.GET['start_date'])
        end_date = getDate_from_string(request.GET['end_date'])

        combined_data = SalesBillEntry.objects.filter(date__range=(start_date, end_date),
                                                      shop=shop_detail_object).values('date').annotate(
            total_rmc=Sum('rmc'),
            total_bags=Sum('salesbillitem__bags'),
            total_total_amount=Sum('total_amount'),
            total_paid_amount=Sum('paid_amount'),
            total_balance_amount=Sum('balance_amount')
        )

        data = []
        # Loop through and print the combined data
        for entry in combined_data:
            single_entry = {
                "Date": entry['date'],
                "Total_RMC": entry['total_rmc'],
                "Total_Amount": entry['total_total_amount'],
                "Total_Paid": entry['total_paid_amount'],
                "Total_Balance": entry['total_balance_amount'],
                "Total_Bags": entry['total_bags'],
            }
            data.append(single_entry)
        return JsonResponse(data={'FOUND': True, 'result': data}, status=status.HTTP_200_OK)
    except Exception as error:
        return JsonResponse(data={'FOUND': False, 'result': error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_all_farmer_name(request):
    [...]
    farmer_name_list = []
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

    lorry_number = request.GET['lorry_number']
    patti_date = getDate_from_string(request.GET['patti_date'])

    arrival_detail_object = ArrivalEntry.objects.get(
        shop=shop_detail_object,
        lorry_no=lorry_number,
        date=patti_date)

    arrival_good_object = ArrivalGoods.objects.filter(
        shop=shop_detail_object,
        arrival_entry=arrival_detail_object,
        patti_status=False
    )

    for arrival_goods_entry in arrival_good_object:
        farmer_name_list.append(arrival_goods_entry.former_name)

    data = {'farmer_list': farmer_name_list}
    return Response(data, status=status.HTTP_200_OK)


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_sales_list_for_arrival_item_list(request):
    [...]

    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

    lorry_number = request.GET['patti_lorry']
    patti_date = getDate_from_string(request.GET['patti_date'])
    patti_farmer = request.GET['patti_farmer']

    arrival_detail_object = ArrivalEntry.objects.get(
        shop=shop_detail_object,
        lorry_no=lorry_number,
        date=patti_date)

    arrival_good_object = ArrivalGoods.objects.filter(
        shop=shop_detail_object,
        arrival_entry=arrival_detail_object,
        former_name=patti_farmer,
        patti_status=False
    )

    advance = 0

    sales_array = []
    arrival_entry_with_no_sales = []
    for arrival_single_goods in arrival_good_object:
        print(arrival_single_goods.id)
        if float(arrival_single_goods.advance) > 0:
            advance = arrival_single_goods.advance

        sales_item_list = SalesBillItem.objects.filter(
            arrival_goods=arrival_single_goods
        )
        if len(sales_item_list) <= 0:
            arrival_entry_with_no_sales.append(arrival_single_goods)
        else:
            for sales in sales_item_list:
                sales_array.append(sales)

    sales_response_list = []
    for single_sales in sales_array:
        sales_dict = {
            'item_name': single_sales.item_name,
            'net_weight': single_sales.net_weight,
            'sold_qty': single_sales.bags}

        arrival_good_object = ArrivalGoods.objects.get(
            id=single_sales.arrival_goods.id,
        )

        sales_dict['lot_number'] = arrival_good_object.remarks
        sales_dict['arrival_qty'] = arrival_good_object.qty
        sales_dict['rates'] = single_sales.rates
        sales_dict['amount'] = single_sales.amount

        sales_response_list.append(sales_dict)

    for single_arrival_entry in arrival_entry_with_no_sales:
        arrival_single_entry = {
            'item_name': single_arrival_entry.item_name,
            'net_weight': single_arrival_entry.weight,
            'sold_qty': 0,
            'lot_number': single_arrival_entry.remarks,
            'arrival_qty': single_arrival_entry.qty,
            'rates': 0,
            'amount': 0
        }
        sales_response_list.append(arrival_single_entry)

    sales_response_list = grouping_sales_bill_entry(sales_response_list)

    data = {
        'farmer_advance': advance,
        'sales_goods_list': sales_response_list
    }

    return Response(data, status=status.HTTP_200_OK)


def grouping_sales_bill_entry(sales_response_list: list):
    group_list = {}
    response = []
    for index, single_item in enumerate(sales_response_list):
        if single_item['lot_number'] not in group_list:
            group_list[single_item['lot_number']] = single_item
        else:
            temp_dict = group_list[single_item['lot_number']]
            temp_dict['sold_qty'] = float(
                temp_dict['sold_qty']) + float(single_item['sold_qty'])
            temp_dict['amount'] = float(
                temp_dict['amount']) + float(single_item['amount'])
            temp_dict['net_weight'] = float(
                temp_dict['net_weight']) + float(single_item['net_weight'])
            temp_dict['rates'] = (
                temp_dict['amount'] / temp_dict['net_weight']) * float(temp_dict['sold_qty'])
            group_list[single_item['lot_number']] = temp_dict

    for value in group_list.values():
        response.append(value)
    return response


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
            (Q(qty__gte=1) | Q(id__in=selected_arrival_goods_ids))
        )

        return render(request, 'Entry/Sales/modify_sales_bill_entry.html',
                      {'sales_bill_detail': False,
                       "arrival_goods_detail": arrival_detail_object,
                       "sales_obj": sales_obj,
                       "sales_item_objs": sales_item_objs
                       }
                      )
    return render(request, 'index.html')


@api_view(['GET'])
def search_customer_ledger(request):
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    customerLedgerObject = CustomerLedger.objects.filter(shop=shop_detail_object).filter(
        name__icontains=request.GET['search_text']) | CustomerLedger.objects.filter(shop=shop_detail_object).filter(
        contact__icontains=request.GET['search_text']) | CustomerLedger.objects.filter(shop=shop_detail_object).filter(
        address__icontains=request.GET['search_text'])
    response = []
    for customer in customerLedgerObject:
        customer_dict = {
            'id': customer.id,
            'name': customer.name,
            'contact': customer.contact,
            'address': customer.address
        }
        response.append(customer_dict)
    if len(response) >= 1:
        return JsonResponse(data={'FOUND': True, 'result': response}, status=status.HTTP_200_OK)
    else:
        return JsonResponse(data={'FOUND': False}, status=status.HTTP_404_NOT_FOUND)


def default_customer_ledger(request, current_page=1, customer_ledger_entry=None):
    if request.user.is_authenticated:
        if customer_ledger_entry is None:
            customer_ledger_entry = {
                "name": "",
                "contact": "",
                "address": "",
                "id": None
            }
        items_per_page = 10
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        request.session['form_token'] = utility.generate_unique_number()
        customer_ledger_list = CustomerLedger.objects.filter(
            shop=shop_detail_object).order_by('-id')
        paginator = Paginator(customer_ledger_list, items_per_page)
        customer_ledger_list = paginator.get_page(current_page)
        response = [
            {
                'id': customer.id,
                'name': customer.name,
                'contact': customer.contact,
                'address': customer.address
            }
            for customer in customer_ledger_list
        ]
        if len(response) >= 1:
            return JsonResponse(data={'FOUND': True, 'result': response}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(data={'FOUND': False}, status=status.HTTP_404_NOT_FOUND)


def get_sales_bill_detail_from_db(shop_detail_object, date):
    selected_date = getDate_from_string(date)

    response = SalesBillEntry.objects.filter(
        date=selected_date,
        shop=shop_detail_object,
    ). \
        values('id', 'customer_name', 'payment_type', 'total_amount', 'balance_amount'). \
        annotate(
        item_name=models.F('sales_bill_item__item_name'),
        bags=models.F('sales_bill_item__bags'),
    )

    if len(response) <= 0:
        response = None
    else:
        result = []
        for single_response in response:
            my_dict = {
                'id': single_response.get('id'),
                'customer_name': single_response.get('customer_name'),
                'item_name': single_response.get('item_name'),
                'bags': single_response.get('bags'),
                'amount': single_response.get('total_amount'),
                'balance': single_response.get('balance_amount'),
                'payment_type': single_response.get('payment_type')
            }
            result.append(my_dict)
        response = consolidate_result_for_report(result)
    return response


@api_view(['GET'])
def report_sales_bill(request):
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    date = request.GET['date']
    response = get_sales_bill_detail_from_db(shop_detail_object, date)
    print(response)
    return JsonResponse(data={'FOUND': True, 'result': response}, status=status.HTTP_200_OK)


@csrf_protect
def report(request):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        return render(request, 'report.html', {
            'shop_details': shop_detail_object,
        })
    return render(request, 'index.html')


@csrf_protect
def sales_bill_report(request):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        return render(request, 'Report/sales_bill_report.html', {
            'shop_details': shop_detail_object,
        })
    return render(request, 'index.html')


@csrf_protect
def rmc_report(request):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        return render(request, 'Report/rmc_report.html', {
            'shop_details': shop_detail_object,
        })
    return render(request, 'index.html')


def extract_dictionary_into_list_container(response):
    list_container = []
    for single_item in response:
        value_list = list(single_item.values())
        list_container.append(value_list)
    return list_container


def generate_sales_bill_report(request):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        response = get_sales_bill_detail_from_db(
            shop_detail_object, request.POST['sales_bill_date'])
        response = extract_dictionary_into_list_container(response)
        return Report.generate_sales_bill_table_report(response)
    return render(request, 'index.html')


def generate_patti_bill_report(request):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

    return render(request, 'index.html')


@csrf_protect
def edit_customer_ledger(request, customer_id):
    if request.user.is_authenticated:
        customer_ledger_detail = CustomerLedger.objects.get(pk=customer_id)
        return customer_ledger(request, customer_ledger_entry=customer_ledger_detail)
    return render(request, 'index.html')


@csrf_protect
def delete_customer_ledger(request, customer_id):
    if request.user.is_authenticated:
        customer_ledger_detail = CustomerLedger.objects.get(pk=customer_id)
        customer_ledger_detail.delete()
        return customer_ledger(request)
    return render(request, 'index.html')
