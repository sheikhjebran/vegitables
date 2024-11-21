from datetime import date
import re

from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_protect

from ..models import Shop, PattiEntry, PattiEntryList, ArrivalEntry, ArrivalGoods, Index
from ..report.report import Report
from ..utility import getDate_from_string


def patti_list(request, current_page=1):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        patti_entry_detail = None
        try:
            patti_entry_detail = PattiEntry.objects.filter(shop=shop_detail_object).filter(Empty_data=False).order_by(
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


def add_new_patti_entry(request):
    if request.user.is_authenticated:
        today = date.today()
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

        index = get_object_or_404(Index, shop=shop_detail_object)

        patti_index = {
            'patti_entry_prefix': index.patti_entry_prefix,
            'patti_entry_counter': int(index.patti_entry_counter) + 1
        }

        return render(request, 'Entry/Patti/modify_patti_entry.html',
                      {
                       "today": today,
                       "new": True,
                       "patti_index": patti_index}
                      )
    return render(request, 'index.html')

def generate_patti_pdf_bill(request):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

        if str(request.POST['new']) == "True":

            patti_entry_obj = PattiEntry.objects.get(
                id=request.POST['patti_bill_id'])
            patti_entry_obj.lorry_no = request.POST['patti_lorry_number']
            patti_entry_obj.shop = shop_detail_object
            patti_entry_obj.date = getDate_from_string(
                request.POST['patti_entry_date'])
            patti_entry_obj.advance = request.POST['advance_amount']
            patti_entry_obj.farmer_name = request.POST['patti_farmer_name']
            patti_entry_obj.total_weight = request.POST['total_weight']
            patti_entry_obj.hamali = request.POST['hamali']
            patti_entry_obj.net_amount = request.POST['net_amount']
            patti_entry_obj.Empty_data = False

        patti_entry_obj.save()
        print(f"New Patti entry item  = {patti_entry_obj.id}")
        if str(request.POST['new']) == "True":
            index_obj = get_object_or_404(Index, shop=shop_detail_object)

            # Increment the arrival_entry_counter
            index_obj.patti_entry_counter += 1
            index_obj.save()


        arrival_detail_object = ArrivalEntry.objects.get(
            shop=shop_detail_object,
            lorry_no=request.POST['patti_lorry_number'],
            date=getDate_from_string(request.POST['patti_entry_date']))

        arrival_good_object = ArrivalGoods.objects.get(
            shop=shop_detail_object,
            arrival_entry=arrival_detail_object,
            former_name=request.POST['patti_farmer_name'],

        )
        arrival_good_object.patti_status = True
        arrival_good_object.save()

        add_patti_item_list(request, list(request.POST), patti_entry_obj)
        return Report.patti_report_view(request)
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
