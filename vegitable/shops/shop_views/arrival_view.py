from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_protect
from datetime import date
import re
from ..models import Shop, ArrivalEntry, ArrivalGoods, Index
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages, auth
from ..utility import getDate_from_string


def add_new_arrival_entry(request):
    if request.user.is_authenticated:
        today = date.today()
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        index = get_object_or_404(Index, shop=shop_detail_object)

        arrival_index = {
            'arrival_entry_prefix': index.arrival_entry_prefix,
            'arrival_entry_counter': int(index.arrival_entry_counter)+1
        }

        return render(request, 'Entry/Arrival/modify_arrival_entry.html', {
            "today": today,
            "new": True,
            "arrival_detail": arrival_index
        })
    return render(request, 'index.html')


@csrf_protect
def add_arrival(request):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

        if str(request.POST['new']) == "True":
            arrival_entry_obj = ArrivalEntry(
                arrival_id=request.POST['arrival_id'],  # for indexing
                gp_no=request.POST['gp_number'],
                date=getDate_from_string(request.POST['arrival_entry_date']),
                patti_name=request.POST['patti_name'],
                total_bags=request.POST['total_number_of_bags'],
                lorry_no=request.POST['lorry_number'],
                shop=shop_detail_object,
                Empty_data=False)
        else:
            arrival_entry_obj = ArrivalEntry.objects.get(
                id=request.POST['id'])  # object to update
            arrival_entry_obj.gp_no = request.POST['gp_number']
            arrival_entry_obj.date = getDate_from_string(
                request.POST['arrival_entry_date'])
            arrival_entry_obj.patti_name = request.POST['patti_name']
            arrival_entry_obj.total_bags = request.POST['total_number_of_bags']
            arrival_entry_obj.lorry_no = request.POST['lorry_number']
            arrival_entry_obj.shop = shop_detail_object
            arrival_entry_obj.Empty_data = False

        arrival_entry_obj.save()
        print(f"New arrival entry  = {arrival_entry_obj.id}")

        if str(request.POST['new']) == "True":
            index_obj = get_object_or_404(Index, shop=shop_detail_object)

            # Increment the arrival_entry_counter
            index_obj.arrival_entry_counter += 1
            index_obj.save()

        add_arrival_goods_item(request, list(
            request.POST), arrival_entry_obj, shop_detail_object)

        return home(request)

    return render(request, 'index.html')


@csrf_protect
def modify_arrival(request, arrival_id):
    if request.user.is_authenticated:
        arrival_entry_obj = ArrivalEntry.objects.get(pk=arrival_id)
        arrival_goods_objs = ArrivalGoods.objects.filter(
            arrival_entry=arrival_entry_obj).order_by('-id')

        today = arrival_entry_obj.date

        return render(request, 'Entry/Arrival/modify_arrival_entry.html',
                      {'arrival_detail': arrival_entry_obj, 'arrival_goods_objs': arrival_goods_objs, 'new': False,
                       "today": today})
    return render(request, 'index.html')


def add_arrival_goods_item(request, request_list, arrival, shop_obj):
    if request.user.is_authenticated:
        former_name_list = []
        item_name_list = []
        qty_list = []
        weight_list = []
        remarks_list = []
        arrival_goods_id = []
        advance_amount_list = []

        for i in request_list:
            former_name_regrex = re.search("^.*_farmer_name$", i)
            if former_name_regrex:
                former_name_list.append(i)

            item_name_regrex = re.search("^.*_item_name$", i)
            if item_name_regrex:
                item_name_list.append(i)

            qty_regrex = re.search("^.*_qty$", i)
            if qty_regrex:
                qty_list.append(i)

            weight_regrex = re.search("^.*_weight$", i)
            if weight_regrex:
                weight_list.append(i)

            remark_regrex = re.search("^.*_remark$", i)
            if remark_regrex:
                remarks_list.append(i)

            advance_amount_regrex = re.search("^.*_advance_amount$", i)
            if advance_amount_regrex:
                advance_amount_list.append(i)

            arrival_goods_id_regrex = re.search("^.*_arrival_goods_id$", i)
            if arrival_goods_id_regrex:
                arrival_goods_id.append(i)

        for i in range(0, len(former_name_list)):
            if "modify" in item_name_list[i]:
                local_id = request.POST[arrival_goods_id[i]].split("_")[0]
                # object to update
                arrival_goods_obj = ArrivalGoods.objects.get(id=int(local_id))
                arrival_goods_obj.item_name = request.POST[item_name_list[i]]
                arrival_goods_obj.former_name = request.POST[former_name_list[i]]
                arrival_goods_obj.initial_qty = request.POST[qty_list[i]]
                arrival_goods_obj.qty = request.POST[qty_list[i]]
                arrival_goods_obj.advance = request.POST[advance_amount_list[i]]
                arrival_goods_obj.weight = request.POST[weight_list[i]]
                arrival_goods_obj.remarks = request.POST[remarks_list[i]]

                arrival_goods_obj.save()
                print(f"Update Arrival Goods item  = {arrival_goods_obj.id}")

            else:

                arrival_goods_obj = ArrivalGoods(
                    item_name=request.POST[item_name_list[i]],
                    shop=shop_obj,
                    arrival_entry=arrival,
                    former_name=request.POST[former_name_list[i]],
                    advance=request.POST[advance_amount_list[i]],
                    initial_qty=request.POST[qty_list[i]],
                    qty=request.POST[qty_list[i]],
                    weight=request.POST[weight_list[i]],
                    remarks=request.POST[remarks_list[i]],
                )

                arrival_goods_obj.save()
                print(f"New Arrival Goods item  = {arrival_goods_obj.id}")
    return render(request, 'index.html')

@csrf_protect
def home(request, current_page=1):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        arrival_entry_detail = None
        try:

            arrival_entry_detail = ArrivalEntry.objects.filter(shop=shop_detail_object).filter(
                Empty_data=False).order_by('-id')
            items_per_page = 10
            paginator = Paginator(arrival_entry_detail, items_per_page)
            arrival_entry_detail = paginator.get_page(current_page)

        except Exception as error:
            print(error)

        return render(request, 'Entry/Arrival/home.html',
                      {
                          'shop_details': shop_detail_object,
                          'arrival_detail': arrival_entry_detail,
                          'current_page': current_page,

                      })

    return render(request, 'index.html')


@csrf_protect
def get_authenticate(request):
    user = auth.authenticate(
        username=request.POST['username'], password=request.POST['password'])
    if user is not None:
        auth.login(request, user)
        return home(request)
    else:
        messages.info(request, 'Invalid Email or Password')
        return redirect('index')


def home_next_page(request, page_number):
    return home(request, current_page=page_number + 1)


def home_prev_page(request, page_number):
    if page_number > 1:
        return home(request, current_page=page_number - 1)
    else:
        return home(request)