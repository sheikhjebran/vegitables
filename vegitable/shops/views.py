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
from django.core.paginator import Paginator
from . import utility
from .repositories.shop_metadata_repository import ShopMetadataRepository
from .report.report import Report
from .repositories.arrival_repository import ArrivalRepository
from .repositories.sales_bill_repository import SalesBillRepository
from .utility import consolidate_result_for_report, get_float_number, getDate_from_string


arrival_repository = ArrivalRepository()
sales_bill_repository = SalesBillRepository()
shop_metadata_repository = ShopMetadataRepository()


def _arrival_firebase_required_message():
    return 'Enable USE_FIREBASE_ARRIVAL=True. SQL arrival path has been removed from shared helpers.'


def _sales_firebase_required_message():
    return 'Enable USE_FIREBASE_SALES=True. SQL sales path has been removed from shared helpers.'


def _load_shop_metadata(user_id):
    return shop_metadata_repository.require_by_owner_user_id(user_id)


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
        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)

        if not arrival_repository.using_firebase():
            return JsonResponse({'error': _arrival_firebase_required_message()}, status=400)

        entries = arrival_repository.build_inventory_entries(shop_detail_object.pk)

        items_per_page = 10
        paginator = Paginator(entries, items_per_page)
        entries = paginator.get_page(current_page)
        return render(request, 'Inventory/inventory.html', {'entries_list': entries,
                                                            'current_page': current_page})
    return render(request, 'index.html')


def profile(request):
    if request.user.is_authenticated:
        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)

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
    if not request.user.is_authenticated:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    item_name_list = {}
    try:
        shop_detail_object = _load_shop_metadata(request.user.id)
    except ValueError as error:
        return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)

    if not arrival_repository.using_firebase():
        return Response({'error': _arrival_firebase_required_message()}, status=status.HTTP_400_BAD_REQUEST)

    _, arrival_goods = arrival_repository.get_goods_by_local_id(
        shop_detail_object.pk,
        request.GET['selected_lot'],
    )
    if arrival_goods is not None:
        item_name_list[arrival_goods.item_name] = arrival_goods.qty

    data = {'item_name_list': item_name_list}
    return Response(data, status=status.HTTP_200_OK)


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_arrival_goods_api(request):
    [...]
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        shop_detail_object = _load_shop_metadata(request.user.id)
    except ValueError as error:
        return JsonResponse({'error': str(error)}, status=400)
    mylist = {}

    if not arrival_repository.using_firebase():
        return JsonResponse({'error': _arrival_firebase_required_message()}, status=400)

    for _, item in arrival_repository.list_available_goods_by_shop(shop_detail_object.pk):
        mylist[item.local_id] = item.qty

    return JsonResponse(mylist, status=status.HTTP_200_OK)


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_arrival_duplicate_validation_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        shop_detail_object = _load_shop_metadata(request.user.id)
    except ValueError as error:
        return JsonResponse({'error': str(error)}, status=400)

    if not arrival_repository.using_firebase():
        return JsonResponse({'error': _arrival_firebase_required_message()}, status=400)

    responses = arrival_repository.find_duplicate(
        shop_id=shop_detail_object.pk,
        lorry_no=request.GET['lorry_no'],
        date=request.GET['date'],
    )
    found = len(responses) > 0

    if not found:
        return JsonResponse(data={'NOT_FOUND': True}, status=status.HTTP_200_OK)
    else:
        return JsonResponse(data={'NOT_FOUND': False}, status=status.HTTP_404_NOT_FOUND)


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_arrival_goods_list(request):
    [...]
    if not request.user.is_authenticated:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    item_goods_list = {}
    try:
        shop_detail_object = _load_shop_metadata(request.user.id)
    except ValueError as error:
        return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)

    if not arrival_repository.using_firebase():
        return Response({'error': _arrival_firebase_required_message()}, status=status.HTTP_400_BAD_REQUEST)

    for _, arrival_entry in arrival_repository.list_available_goods_by_shop(shop_detail_object.pk):
        item_goods_list[arrival_entry.local_id] = arrival_entry.remarks

    data = {'item_goods_list': item_goods_list}
    return Response(data, status=status.HTTP_200_OK)


def get_sales_bill_detail_from_db(shop_detail_object, date):
    selected_date = getDate_from_string(date)

    if not sales_bill_repository.using_firebase():
        raise ValueError(_sales_firebase_required_message())

    result = []
    selected_date_iso = selected_date.isoformat()
    for sales_record in sales_bill_repository.list_by_shop(shop_detail_object.pk):
        if str(sales_record.date) != selected_date_iso:
            continue
        for item in sales_record.items:
            result.append({
                'id': sales_record.sales_bill_id,
                'customer_name': sales_record.customer_name,
                'item_name': item.item_name,
                'bags': item.bags,
                'amount': sales_record.total_amount,
                'balance': sales_record.balance_amount,
                'payment_type': sales_record.payment_type,
            })

    if len(result) <= 0:
        return None
    return consolidate_result_for_report(result)


@api_view(['GET'])
def report_sales_bill(request):
    try:
        shop_detail_object = _load_shop_metadata(request.user.id)
    except ValueError as error:
        return JsonResponse(data={'FOUND': False, 'error': str(error)}, status=400)
    date = request.GET['date']

    try:
        response = get_sales_bill_detail_from_db(shop_detail_object, date)
    except ValueError as error:
        return JsonResponse(data={'FOUND': False, 'error': str(error)}, status=400)

    print(response)
    return JsonResponse(data={'FOUND': True, 'result': response}, status=status.HTTP_200_OK)


@csrf_protect
def report(request):
    if request.user.is_authenticated:
        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)
        return render(request, 'report.html', {
            'shop_details': shop_detail_object,
        })
    return render(request, 'index.html')


@csrf_protect
def sales_bill_report(request):
    if request.user.is_authenticated:
        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)
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
        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)

        try:
            response = get_sales_bill_detail_from_db(
                shop_detail_object, request.POST['sales_bill_date'])
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)

        response = extract_dictionary_into_list_container(response)
        return Report.generate_sales_bill_table_report(response)
    return render(request, 'index.html')


def generate_patti_bill_report(request):
    if request.user.is_authenticated:
        try:
            _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)

    return render(request, 'index.html')


def view_pdf(request, file_name):
    pdf_path = os.path.join(settings.MEDIA_ROOT, file_name)

    # 🔥 Ensure file exists before returning
    if not os.path.exists(pdf_path):
        raise Http404("File not found")

    # Serve the PDF file
    return FileResponse(open(pdf_path, "rb"), content_type="application/pdf")