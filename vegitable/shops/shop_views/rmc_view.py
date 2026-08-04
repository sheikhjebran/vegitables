from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.decorators import api_view
import datetime
from xhtml2pdf import pisa
from ..models import Shop, SalesBillEntry
from ..repositories.sales_bill_repository import SalesBillRepository
from ..utility import getDate_from_string
from django.db.models import Sum, F, Q
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import redirect, render, get_object_or_404


sales_bill_repository = SalesBillRepository()


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


def build_daily_rmc_data(shop_id, rmc_date):
    if sales_bill_repository.using_firebase():
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

    queryset = SalesBillEntry.objects.filter(shop=shop_id, date=rmc_date).annotate(
        total_bags=Sum('salesbillitem__bags'),
        total_paid_amount=F('paid_amount'),
        total_rmc=F('rmc')
    ).values('id', 'payment_type', 'total_bags', 'total_paid_amount', 'total_rmc')

    data = []
    for entry in queryset:
        data.append({
            'entry_id': entry['id'],
            'payment_type': entry['payment_type'],
            'bags': entry['total_bags'],
            'paid_amount': entry['total_paid_amount'],
            'rmc': entry['total_rmc'],
        })
    return data


def build_weekly_rmc_data(shop_id, start_date, end_date):
    if sales_bill_repository.using_firebase():
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

    combined_data = SalesBillEntry.objects.filter(date__gte=start_date, date__lte=end_date,
                                                  shop=shop_id).values('date').annotate(
        total_rmc=Sum('rmc'),
        total_bags=Sum('salesbillitem__bags'),
        total_total_amount=Sum('total_amount'),
        total_paid_amount=Sum('paid_amount'),
        total_balance_amount=Sum('balance_amount')
    )

    data = []
    for entry in combined_data:
        data.append({
            'Date': entry['date'],
            'Total_RMC': entry['total_rmc'],
            'Total_Amount': entry['total_total_amount'],
            'Total_Paid': entry['total_paid_amount'],
            'Total_Balance': entry['total_balance_amount'],
            'Total_Bags': entry['total_bags'],
        })
    return data


@csrf_protect
def rmc_report(request):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        return render(request, 'Report/rmc_report.html', {
            'shop_details': shop_detail_object,
        })
    return render(request, 'index.html')


@api_view(('GET',))
def get_daily_rmc_start_and_end_date(request):
    [...]
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
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
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    try:
        rmc_date = getDate_from_string(request.GET['date'])
        data = build_daily_rmc_data(shop_detail_object.pk, rmc_date)

        if len(data) > 0:
            return JsonResponse(data={'FOUND': True, 'result': data}, status=status.HTTP_200_OK)
        return JsonResponse(data={'FOUND': False, 'result': data}, status=status.HTTP_200_OK)
    except Exception as error:
        return JsonResponse(data={'FOUND': False, 'result': error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def print_rmc_weekly_report(request):
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    start_date = getDate_from_string(request.GET['start_date'])
    end_date = getDate_from_string(request.GET['end_date'])
    if start_date and end_date:
        if sales_bill_repository.using_firebase():
            data = []
            for record in _firebase_sales_between_dates(shop_detail_object.pk, start_date, end_date):
                data.append({
                    'date': record.date,
                    'rmc': round(float(record.rmc), 2),
                    'salesbillitem__bags': sum(int(item.bags) for item in record.items),
                    'total_amount': round(float(record.total_amount), 2),
                    'paid_amount': round(float(record.paid_amount), 2),
                    'balance_amount': round(float(record.balance_amount), 2),
                })
        else:
            data = SalesBillEntry.objects.filter(date__gte=start_date, date__lte=end_date, shop=shop_detail_object).values(
                'date', 'rmc', 'salesbillitem__bags', 'total_amount', 'paid_amount', 'balance_amount'
            )
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
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    selected_date = getDate_from_string(request.GET['date'])
    if selected_date:
        if sales_bill_repository.using_firebase():
            data = []
            for record in _firebase_sales_by_date(shop_detail_object.pk, selected_date):
                data.append({
                    'date': record.date,
                    'rmc': round(float(record.rmc), 2),
                    'salesbillitem__bags': sum(int(item.bags) for item in record.items),
                    'total_amount': round(float(record.total_amount), 2),
                    'paid_amount': round(float(record.paid_amount), 2),
                    'balance_amount': round(float(record.balance_amount), 2),
                })
        else:
            data = SalesBillEntry.objects.filter(date=selected_date, shop=shop_detail_object).values(
                'date', 'rmc', 'salesbillitem__bags', 'total_amount', 'paid_amount', 'balance_amount'
            )
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
