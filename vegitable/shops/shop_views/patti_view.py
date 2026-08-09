import os
import re
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.decorators import renderer_classes, api_view
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.response import Response
from ..models import Shop
from ..repositories.arrival_repository import ArrivalRepository
from ..repositories.patti_repository import PattiRepository
from ..repositories.sales_bill_repository import SalesBillRepository
from ..repositories.shop_metadata_repository import ShopMetadataRepository
from ..utility import getDate_from_string
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.conf import settings
import uuid


arrival_repository = ArrivalRepository()
sales_bill_repository = SalesBillRepository()
patti_repository = PattiRepository()
shop_metadata_repository = ShopMetadataRepository()


def _patti_firebase_required_message():
    return 'Enable USE_FIREBASE_PATTI=True. SQL patti path has been removed.'


def _arrival_firebase_required_message():
    return 'Enable USE_FIREBASE_ARRIVAL=True. SQL arrival path has been removed from patti workflows.'


def _sales_firebase_required_message():
    return 'Enable USE_FIREBASE_SALES=True. SQL sales path has been removed from patti workflows.'


def _load_shop_metadata(user_id):
    return shop_metadata_repository.require_by_owner_user_id(user_id)


def _belongs_to_shop(record, shop_id):
    return record is not None and int(record.shop_id) == int(shop_id)

def patti_entry(request, current_page=1):
    if request.user.is_authenticated:
        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)

        if not patti_repository.using_firebase():
            return JsonResponse({'error': _patti_firebase_required_message()}, status=400)

        patti_entry_detail = []
        try:
            patti_entry_detail = patti_repository.list_by_shop(shop_detail_object.pk)

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


def get_unsettled_lorry_details(shop_detail_object):
    if not arrival_repository.using_firebase():
        raise ValueError(_arrival_firebase_required_message())

    return [
        {
            'id': record.id,
            'lorry_no': record.lorry_no,
        }
        for record in arrival_repository.list_unsettled_entries(shop_detail_object.pk)
    ]


def add_new_patti_entry(request):
    if request.user.is_authenticated:
        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)

        if not patti_repository.using_firebase():
            return JsonResponse({'error': _patti_firebase_required_message()}, status=400)

        patti_index = {
            'patti_entry_prefix': shop_detail_object.patti_entry_prefix,
            'patti_entry_counter': int(shop_detail_object.patti_entry_counter) + 1
        }

        try:
            un_settled_lorry_detail = get_unsettled_lorry_details(shop_detail_object)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)
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
    if not request.user.is_authenticated:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    arrival_entry_id = request.GET['lorry_number']
    try:
        shop_detail_object = _load_shop_metadata(request.user.id)
    except ValueError as error:
        return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)

    if not arrival_repository.using_firebase():
        return Response({'error': _arrival_firebase_required_message()}, status=status.HTTP_400_BAD_REQUEST)

    former_names = arrival_repository.list_unsettled_farmer_names(
        shop_detail_object.pk,
        arrival_entry_id,
    )
    return Response({'farmer_list': former_names}, status=status.HTTP_200_OK)


def view_generate_patti_pdf_bill(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized access'}, status=403)

    try:
        shop_detail_object = _load_shop_metadata(request.user.id)
    except ValueError as error:
        return JsonResponse({'error': str(error)}, status=400)

    if not patti_repository.using_firebase():
        return JsonResponse({'error': _patti_firebase_required_message()}, status=400)
    if not arrival_repository.using_firebase():
        return JsonResponse({'error': _arrival_firebase_required_message()}, status=400)

    is_new = str(request.POST.get('new')) == "True"

    if is_new:
        try:
            patti_items = build_patti_item_list(request, list(request.POST))

            patti_entry_obj = patti_repository.create(
                shop_id=shop_detail_object.pk,
                lorry_no=request.POST['patti_lorry_number'],
                date=getDate_from_string(request.POST['patti_entry_date']),
                advance=request.POST['advance_amount'],
                farmer_name=request.POST['patti_farmer_name'],
                total_weight=request.POST['total_weight'],
                hamali=request.POST['hamali'],
                net_amount=request.POST['net_amount'],
                patti_id=request.POST['patti_bill_id'],
                items=patti_items,
            )

            shop_metadata_repository.increment_counter(request.user.id, 'patti_entry_counter')

            settled_count = arrival_repository.mark_goods_settled(
                shop_id=shop_detail_object.pk,
                entry_id=request.POST['patti_lorry_number'],
                former_name=request.POST['patti_farmer_name'],
            )
            if settled_count <= 0:
                return JsonResponse({'error': 'No matching ArrivalGoods found'}, status=404)

            pdf_url = generate_patti_pdf(request, patti_entry_obj)
            return JsonResponse({'pdf_url': pdf_url}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    if str(request.POST.get('new')) == "False":
        try:
            existing_record = patti_repository.get_by_id(request.POST['id'])
            if not _belongs_to_shop(existing_record, shop_detail_object.pk):
                return JsonResponse({'error': 'Patti entry does not belong to your shop.'}, status=403)

            patti_items = build_patti_item_list(request, list(request.POST))
            patti_entry_obj = patti_repository.update(
                record_id=request.POST['id'],
                shop_id=shop_detail_object.pk,
                lorry_no=request.POST['patti_lorry_number'],
                date=getDate_from_string(request.POST['patti_entry_date']),
                advance=request.POST['advance_amount'],
                farmer_name=request.POST['patti_farmer_name'],
                total_weight=request.POST['total_weight'],
                hamali=request.POST['hamali'],
                net_amount=request.POST['net_amount'],
                patti_id=request.POST['patti_bill_id'],
                items=patti_items,
            )

            pdf_url = generate_patti_pdf(request, patti_entry_obj)
            return JsonResponse({'pdf_url': pdf_url}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)


def generate_patti_pdf(request, patti_entry_obj):
    data = [
        {
            'date': patti_entry_obj.date,
            'item': patti_entry_obj.farmer_name,
            'quantity': patti_entry_obj.total_weight,
            'rate': patti_entry_obj.hamali,
            'amount': patti_entry_obj.net_amount
        }
    ]

    # Render data to an HTML template
    html_string = render_to_string(
        'Entry/Patti/report_template/patti_pdf_template.html', {'data': data})

    # Generate PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="patti_bill.pdf"'

    pisa_status = pisa.CreatePDF(html_string, dest=response)

    if pisa_status.err:
        return JsonResponse({'error': 'Error generating PDF'}, status=500)

    # Generate a unique filename
    unique_filename = f"patti_bill_{uuid.uuid4().hex}.pdf"
    pdf_file_path = os.path.join(settings.MEDIA_ROOT, unique_filename)

    # Save the PDF to the static directory
    with open(pdf_file_path, 'wb') as pdf_file:
        pdf_file.write(response.content)

    pdf_url = request.build_absolute_uri(settings.MEDIA_URL + unique_filename)
    return pdf_url


@csrf_protect
def edit_patti_entry(request, patti_id):
    if request.user.is_authenticated:
        if not patti_repository.using_firebase():
            return JsonResponse({'error': _patti_firebase_required_message()}, status=400)

        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)

        patti_bill_detail = patti_repository.get_by_id(patti_id)
        if patti_bill_detail is None:
            return JsonResponse({'error': 'Patti entry not found'}, status=404)
        if not _belongs_to_shop(patti_bill_detail, shop_detail_object.pk):
            return JsonResponse({'error': 'Patti entry does not belong to your shop.'}, status=403)
        today = patti_bill_detail.date
        patti_entry_obj = patti_bill_detail.items

        return render(request, 'Entry/Patti/modify_patti_entry.html',
                      {'patti_bill_detail': patti_bill_detail,
                       "today": today,
                       "patti_entry_obj": patti_entry_obj,
                       "new": False}
                      )
    return render(request, 'index.html')


def build_patti_item_list(request, request_list):
    item_name_list = []
    lot_number_list = []
    weight_list = []
    rate_list = []
    amount_list = []

    for key in request_list:
        if re.search("^.*_item_name$", key):
            item_name_list.append(key)

        if re.search("^.*_lot_number$", key):
            lot_number_list.append(key)

        if re.search("^.*_weight$", key):
            weight_list.append(key)

        if re.search("^.*_rate$", key):
            rate_list.append(key)

        if re.search("^.*_amount$", key):
            amount_list.append(key)

    rows = []
    for index in range(0, len(item_name_list)):
        rows.append(
            {
                'item': request.POST[item_name_list[index]],
                'lot_no': request.POST[lot_number_list[index]],
                'weight': request.POST[weight_list[index]],
                'rate': request.POST[rate_list[index]],
                'amount': request.POST[amount_list[index]],
            }
        )
    return rows


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_sales_list_for_arrival_item_list(request):
    [...]

    if not request.user.is_authenticated:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        shop_detail_object = _load_shop_metadata(request.user.id)
    except ValueError as error:
        return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)

    lorry_number = request.GET['patti_lorry']
    patti_farmer = request.GET['patti_farmer']

    if not arrival_repository.using_firebase():
        return Response({'error': _arrival_firebase_required_message()}, status=status.HTTP_400_BAD_REQUEST)
    if not sales_bill_repository.using_firebase():
        return Response({'error': _sales_firebase_required_message()}, status=status.HTTP_400_BAD_REQUEST)

    arrival_detail_object = arrival_repository.get_by_id(lorry_number)
    if arrival_detail_object is None:
        return JsonResponse({'error': 'No matching ArrivalEntry found'}, status=404)
    if int(arrival_detail_object.shop_id) != int(shop_detail_object.pk):
        return JsonResponse({'error': 'Arrival entry does not belong to your shop.'}, status=403)

    arrival_good_object = [
        goods for goods in arrival_detail_object.goods
        if goods.former_name == patti_farmer and not goods.patti_status
    ]

    advance = 0
    sales_response_list = []
    sales_records = sales_bill_repository.list_by_shop(shop_detail_object.pk)
    sales_items_by_lot = {}
    for record in sales_records:
        for item in record.items:
            sales_items_by_lot.setdefault(str(item.arrival_goods_local_id), []).append(item)

    for arrival_single_goods in arrival_good_object:
        if float(arrival_single_goods.advance) > 0:
            advance = arrival_single_goods.advance

        sales_item_list = sales_items_by_lot.get(str(arrival_single_goods.local_id), [])
        if len(sales_item_list) <= 0:
            sales_response_list.append({
                'item_name': arrival_single_goods.item_name,
                'net_weight': arrival_single_goods.weight,
                'sold_qty': 0,
                'lot_number': arrival_single_goods.remarks,
                'arrival_qty': arrival_single_goods.qty,
                'rates': 0,
                'amount': 0,
            })
            continue

        for single_sales in sales_item_list:
            sales_response_list.append({
                'item_name': single_sales.item_name,
                'net_weight': single_sales.net_weight,
                'sold_qty': single_sales.bags,
                'lot_number': arrival_single_goods.remarks,
                'arrival_qty': arrival_single_goods.qty,
                'rates': single_sales.rates,
                'amount': single_sales.amount,
            })

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
