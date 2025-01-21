from datetime import date
import re
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.decorators import renderer_classes, api_view
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.response import Response
from ..models import Shop, PattiEntry, PattiEntryList, ArrivalEntry, ArrivalGoods, Index, SalesBillItem
from ..report.report import Report
from ..utility import getDate_from_string


def patti_list(request, current_page=1):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        patti_entry_detail = None
        try:
            patti_entry_detail = PattiEntry.objects.filter(shop=shop_detail_object).order_by(
                '-id')
            items_per_page = 10
            paginator = Paginator(patti_entry_detail, items_per_page)
            patti_entry_detail = paginator.get_page(current_page)
        except Exception as error:
            print(error)

        return render(request, 'Entry/Patti/patti.html',
                      {
                          'shop_details': shop_detail_object,
                          'patti_entry_detail': patti_entry_detail,
                          'current_page': current_page
                      })

    return render(request, 'index.html')


def get_unsettled_lorry_details():
    # Filter ArrivalGoods with patti_status as False and get related ArrivalEntry fields
    unsettled_entries = ArrivalEntry.objects.filter(
        arrivalgoods__patti_status=False
    ).distinct().values('id', 'lorry_no')

    return list(unsettled_entries)


def add_new_patti_entry(request):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

        index = get_object_or_404(Index, shop=shop_detail_object)

        patti_index = {
            'patti_entry_prefix': index.patti_entry_prefix,
            'patti_entry_counter': int(index.patti_entry_counter) + 1
        }

        un_settled_lorry_detail = get_unsettled_lorry_details()
        return render(request, 'Entry/Patti/modify_patti_entry.html',
                      {
                          "un_settled_lorry_detail": un_settled_lorry_detail,
                          "new": True,
                          "patti_index": patti_index}
                      )
    return render(request, 'index.html')


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_all_farmer_name(request):
    [...]
    arrival_entry_id = request.GET['lorry_number']
    arrival_entry = get_object_or_404(ArrivalEntry, id=arrival_entry_id)
    former_names = ArrivalGoods.objects.filter(
        arrival_entry=arrival_entry,
        patti_status=False
    ).values_list('former_name', flat=True)
    data = {'farmer_list': list(former_names)}
    return Response(data, status=status.HTTP_200_OK)


def generate_patti_pdf_bill(request):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

        if str(request.POST['new']) == "True":

            patti_entry_obj = PattiEntry(
                lorry_no=request.POST['patti_lorry_number'],
                date=getDate_from_string(
                    request.POST['patti_entry_date']),
                advance=request.POST['advance_amount'],
                farmer_name=request.POST['patti_farmer_name'],
                total_weight=request.POST['total_weight'],
                hamali=request.POST['hamali'],
                net_amount=request.POST['net_amount'],
                shop=shop_detail_object,
                patti_id=request.POST['patti_bill_id']
            )

            patti_entry_obj.save()

        if str(request.POST['new']) == "True":
            index_obj = get_object_or_404(Index, shop=shop_detail_object)

            # Increment the arrival_entry_counter
            index_obj.patti_entry_counter += 1
            index_obj.save()

        arrival_detail_object = ArrivalEntry.objects.get(
            id=request.POST['patti_lorry_number'])

        arrival_good_object = ArrivalGoods.objects.get(
            shop=shop_detail_object,
            arrival_entry=arrival_detail_object,
            former_name=request.POST['patti_farmer_name'],

        )
        arrival_good_object.patti_status = True
        arrival_good_object.save()

        add_patti_item_list(request, list(request.POST), patti_entry_obj)
        # TODO : return Report.patti_report_view(request)
        return patti_list(request)
    return render(request, 'index.html')


@csrf_protect
def edit_patti_entry(request, patti_id):
    if request.user.is_authenticated:
        patti_bill_detail = PattiEntry.objects.get(pk=patti_id)
        today = patti_bill_detail.date

        patti_entry_obj = PattiEntryList.objects.filter(
            patti=patti_bill_detail)

        return render(request, 'Entry/Patti/modify_patti_entry.html',
                      {'patti_bill_detail': patti_bill_detail,
                       "today": today,
                       "patti_entry_obj": patti_entry_obj,
                       "new": False}
                      )
    return render(request, 'index.html')


def add_patti_item_list(request, request_list, patti_entry_obj):
    if request.user.is_authenticated:
        item_name_list = []
        lot_number_list = []
        weight_list = []
        rate_list = []
        amount_list = []

        for i in request_list:
            item_name_list_regrex = re.search("^.*_item_name$", i)
            if item_name_list_regrex:
                item_name_list.append(i)

            lot_number_list_regrex = re.search("^.*_lot_number$", i)
            if lot_number_list_regrex:
                lot_number_list.append(i)

            weight_list_regrex = re.search("^.*_weight$", i)
            if weight_list_regrex:
                weight_list.append(i)

            rate_list_regrex = re.search("^.*_rate$", i)
            if rate_list_regrex:
                rate_list.append(i)

            amount_list_regrex = re.search("^.*_amount$", i)
            if amount_list_regrex:
                amount_list.append(i)

        for i in range(0, len(item_name_list)):
            patti_obj = PattiEntryList(
                item=request.POST[item_name_list[i]],
                lot_no=request.POST[lot_number_list[i]],
                weight=request.POST[weight_list[i]],
                rate=request.POST[rate_list[i]],
                amount=request.POST[amount_list[i]],
                patti=patti_entry_obj
            )

            patti_obj.save()

    return render(request, 'index.html')


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_sales_list_for_arrival_item_list(request):
    [...]

    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

    lorry_number = request.GET['patti_lorry']
    patti_farmer = request.GET['patti_farmer']

    arrival_detail_object = ArrivalEntry.objects.get(
        id=int(lorry_number))

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
