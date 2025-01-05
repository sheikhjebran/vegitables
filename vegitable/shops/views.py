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


def inventory_next_page(request, page_number):
    return inventory(request, current_page=page_number + 1)


def inventory_prev_page(request, page_number):
    if page_number > 1:
        return inventory(request, current_page=page_number - 1)
    else:
        return inventory(request)


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
