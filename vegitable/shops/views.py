import os

from django.conf import settings
from django.http import JsonResponse, Http404, FileResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages, auth
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes, permission_classes
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
from .repositories.arrival_repository import ArrivalRepository
from .utility import consolidate_result_for_report, get_float_number, getDate_from_string
from django.db.models import Sum, F, Q


arrival_repository = ArrivalRepository()


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

        if arrival_repository.using_firebase():
            entries = arrival_repository.build_inventory_entries(shop_detail_object.pk)
        else:
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
    if arrival_repository.using_firebase():
        _, arrival_goods = arrival_repository.get_goods_by_local_id(
            shop_detail_object.pk,
            request.GET['selected_lot'],
        )
        if arrival_goods is not None:
            item_name_list[arrival_goods.item_name] = arrival_goods.qty
    else:
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
    mylist = {}
    if arrival_repository.using_firebase():
        for _, item in arrival_repository.list_available_goods_by_shop(shop_detail_object.pk):
            mylist[item.local_id] = item.qty
    else:
        arrival_goods_obj = ArrivalGoods.objects.filter(
            shop=shop_detail_object, qty__gte=1)

        for item in arrival_goods_obj:
            mylist[item.id] = item.qty

    return JsonResponse(mylist, status=status.HTTP_200_OK)


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_arrival_duplicate_validation_api(request):
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    if arrival_repository.using_firebase():
        responses = arrival_repository.find_duplicate(
            shop_id=shop_detail_object.pk,
            lorry_no=request.GET['lorry_no'],
            date=request.GET['date'],
        )
        found = len(responses) > 0
    else:
        responses = ArrivalEntry.objects.filter(shop=shop_detail_object).filter(lorry_no=request.GET['lorry_no']).filter(
            date=request.GET['date'])
        found = responses.count() > 0

    if not found:
        return JsonResponse(data={'NOT_FOUND': True}, status=status.HTTP_200_OK)
    else:
        return JsonResponse(data={'NOT_FOUND': False}, status=status.HTTP_404_NOT_FOUND)


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_arrival_goods_list(request):
    [...]
    item_goods_list = {}
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    if arrival_repository.using_firebase():
        for _, arrival_entry in arrival_repository.list_available_goods_by_shop(shop_detail_object.pk):
            item_goods_list[arrival_entry.local_id] = arrival_entry.remarks
    else:
        arrival_detail_object = ArrivalGoods.objects.filter(
            shop=shop_detail_object, qty__gte=1)

        for arrival_entry in arrival_detail_object:
            item_goods_list[arrival_entry.id] = arrival_entry.remarks

    data = {'item_goods_list': item_goods_list}
    return Response(data, status=status.HTTP_200_OK)


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


def view_pdf(request, file_name):
    pdf_path = os.path.join(settings.MEDIA_ROOT, file_name)

    # 🔥 Ensure file exists before returning
    if not os.path.exists(pdf_path):
        raise Http404("File not found")

    # Serve the PDF file
    return FileResponse(open(pdf_path, "rb"), content_type="application/pdf")