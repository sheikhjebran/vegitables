from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.decorators import api_view
import datetime
from xhtml2pdf import pisa
from ..models import Shop, SalesBillEntry
from ..utility import getDate_from_string
from django.db.models import Sum, F, Q
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import redirect, render, get_object_or_404


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

        combined_data = SalesBillEntry.objects.filter(date__gte=start_date, date__lte=end_date,
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


def print_rmc_weekly_report(request):
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    start_date = getDate_from_string(request.GET['start_date'])
    end_date = getDate_from_string(request.GET['end_date'])
    if start_date and end_date:
        # Fetch data based on the selected date
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
        # Fetch data based on the selected date
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
