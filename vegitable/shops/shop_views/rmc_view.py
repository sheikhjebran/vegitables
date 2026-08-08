from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.decorators import api_view
import datetime
from xhtml2pdf import pisa
from ..repositories.sales_bill_repository import SalesBillRepository
from ..repositories.shop_metadata_repository import ShopMetadataRepository
from ..utility import getDate_from_string
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render


sales_bill_repository = SalesBillRepository()
shop_metadata_repository = ShopMetadataRepository()


def _shop_pk(shop_or_id):
    return int(getattr(shop_or_id, 'pk', shop_or_id))


def _iso_date(value):
    if isinstance(value, str):
        return value
    return value.isoformat()


def _firebase_sales_by_date(shop_id, selected_date):
    shop_pk = _shop_pk(shop_id)
    target_date = _iso_date(selected_date)
    records = sales_bill_repository.list_by_shop(shop_pk)
    return [record for record in records if str(record.date) == target_date]


def _firebase_sales_between_dates(shop_id, start_date, end_date):
    shop_pk = _shop_pk(shop_id)
    start_iso = _iso_date(start_date)
    end_iso = _iso_date(end_date)
    records = sales_bill_repository.list_by_shop(shop_pk)
    return [
        record for record in records
        if start_iso <= str(record.date) <= end_iso
    ]


def _require_firebase_sales():
    if not sales_bill_repository.using_firebase():
        raise ValueError('Enable USE_FIREBASE_SALES=True for RMC report workflows.')


def _load_shop_metadata(user_id):
    return shop_metadata_repository.require_by_owner_user_id(user_id)


def build_daily_rmc_data(shop_id, rmc_date):
    _require_firebase_sales()

    data = []
    for record in _firebase_sales_by_date(shop_id, rmc_date):
        data.append({
            'entry_id': record.sales_bill_id,
            'payment_type': record.payment_type,
            'bags': sum(int(item.bags) for item in record.items),
            'paid_amount': round(float(record.paid_amount), 2),
            'rmc': round(float(record.rmc), 2),
        })
    return data


def build_weekly_rmc_data(shop_id, start_date, end_date):
    _require_firebase_sales()
    grouped = {}
    for record in _firebase_sales_between_dates(shop_id, start_date, end_date):
        date_key = str(record.date)
        if date_key not in grouped:
            grouped[date_key] = {
                'date': date_key,
                'total_rmc': 0.0,
                'total_total_amount': 0.0,
                'total_paid_amount': 0.0,
                'total_balance_amount': 0.0,
                'total_bags': 0,
            }
        grouped[date_key]['total_rmc'] += float(record.rmc)
        grouped[date_key]['total_total_amount'] += float(record.total_amount)
        grouped[date_key]['total_paid_amount'] += float(record.paid_amount)
        grouped[date_key]['total_balance_amount'] += float(record.balance_amount)
        grouped[date_key]['total_bags'] += sum(int(item.bags) for item in record.items)

    data = []
    for _, entry in sorted(grouped.items(), key=lambda item: item[0]):
        data.append({
            'Date': entry['date'],
            'Total_RMC': round(entry['total_rmc'], 2),
            'Total_Amount': round(entry['total_total_amount'], 2),
            'Total_Paid': round(entry['total_paid_amount'], 2),
            'Total_Balance': round(entry['total_balance_amount'], 2),
            'Total_Bags': entry['total_bags'],
        })
    return data


@csrf_protect
def rmc_report(request):
    if request.user.is_authenticated:
        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)
        return render(request, 'Report/rmc_report.html', {
            'shop_details': shop_detail_object,
        })
    return render(request, 'index.html')


@api_view(('GET',))
def get_daily_rmc_start_and_end_date(request):
    [...]
    try:
        shop_detail_object = _load_shop_metadata(request.user.id)
    except ValueError as error:
        return JsonResponse(data={'FOUND': False, 'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)
    try:
        start_date = getDate_from_string(request.GET['start_date'])

        end_date = getDate_from_string(request.GET['end_date'])
        data = build_weekly_rmc_data(shop_detail_object.pk, start_date, end_date)
        return JsonResponse(data={'FOUND': True, 'result': data}, status=status.HTTP_200_OK)
    except Exception as error:
        return JsonResponse(data={'FOUND': False, 'result': error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(('GET',))
def get_daily_rmc_selected_date(request):
    [...]
    try:
        shop_detail_object = _load_shop_metadata(request.user.id)
    except ValueError as error:
        return JsonResponse(data={'FOUND': False, 'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)
    try:
        rmc_date = getDate_from_string(request.GET['date'])
        data = build_daily_rmc_data(shop_detail_object.pk, rmc_date)

        if len(data) > 0:
            return JsonResponse(data={'FOUND': True, 'result': data}, status=status.HTTP_200_OK)
        return JsonResponse(data={'FOUND': False, 'result': data}, status=status.HTTP_200_OK)
    except Exception as error:
        return JsonResponse(data={'FOUND': False, 'result': error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def print_rmc_weekly_report(request):
    try:
        shop_detail_object = _load_shop_metadata(request.user.id)
    except ValueError as error:
        return JsonResponse({'error': str(error)}, status=400)
    start_date = getDate_from_string(request.GET['start_date'])
    end_date = getDate_from_string(request.GET['end_date'])
    if start_date and end_date:
        try:
            _require_firebase_sales()
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)

        data = []
        records = sorted(
            _firebase_sales_between_dates(shop_detail_object.pk, start_date, end_date),
            key=lambda item: (str(item.date), str(item.sales_bill_id), int(item.created_at_ms)),
        )
        for record in records:
            data.append({
                'sales_bill_id': record.sales_bill_id,
                'date': record.date,
                'rmc': round(float(record.rmc), 2),
                'salesbillitem__bags': sum(int(item.bags) for item in record.items),
                'total_amount': round(float(record.total_amount), 2),
                'paid_amount': round(float(record.paid_amount), 2),
                'balance_amount': round(float(record.balance_amount), 2),
            })
        # Render the data to an HTML template
        html_string = render_to_string(
            'Report/report_template/rmc_weekly_report_template.html', {'data': data})
        # Generate PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="rmc_weekly_report.pdf"'
        pisa_status = pisa.CreatePDF(html_string, dest=response)
        if pisa_status.err:
            return JsonResponse({'error': 'Error generating PDF'}, status=500)
        return response
    else:
        return JsonResponse({'error': 'Invalid date'}, status=400)


def print_rmc_daily_report(request):
    try:
        shop_detail_object = _load_shop_metadata(request.user.id)
    except ValueError as error:
        return JsonResponse({'error': str(error)}, status=400)
    selected_date = getDate_from_string(request.GET['date'])
    if selected_date:
        try:
            _require_firebase_sales()
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)

        data = []
        for record in _firebase_sales_by_date(shop_detail_object.pk, selected_date):
            data.append({
                'sales_bill_id': record.sales_bill_id,
                'date': record.date,
                'rmc': round(float(record.rmc), 2),
                'salesbillitem__bags': sum(int(item.bags) for item in record.items),
                'total_amount': round(float(record.total_amount), 2),
                'paid_amount': round(float(record.paid_amount), 2),
                'balance_amount': round(float(record.balance_amount), 2),
            })
        # Render the data to an HTML template
        html_string = render_to_string(
            'Report/report_template/rmc_daily_report_template.html', {'data': data})
        # Generate PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="rmc_daily_report.pdf"'
        pisa_status = pisa.CreatePDF(html_string, dest=response)
        if pisa_status.err:
            return JsonResponse({'error': 'Error generating PDF'}, status=500)
        return response
    else:
        return JsonResponse({'error': 'Invalid date'}, status=400)
