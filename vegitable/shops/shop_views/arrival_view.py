from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_protect
from datetime import date
import re
from django.shortcuts import redirect, render
from django.contrib import messages, auth
from ..repositories.arrival_repository import ArrivalRepository
from ..repositories.shop_metadata_repository import ShopMetadataRepository
from ..utility import getDate_from_string


arrival_repository = ArrivalRepository()
shop_metadata_repository = ShopMetadataRepository()


def _arrival_firebase_required_message():
    return 'Enable USE_FIREBASE_ARRIVAL=True. SQL arrival path has been removed.'


def _shop_metadata_required_message(error):
    return str(error)


def _belongs_to_shop(record, shop_id):
    return record is not None and int(record.shop_id) == int(shop_id)


def _parse_arrival_goods_payload(request, request_list, existing_goods_status=None):
    former_name_list = []
    item_name_list = []
    qty_list = []
    weight_list = []
    remarks_list = []
    arrival_goods_id = []
    advance_amount_list = []

    for key in request_list:
        if re.search("^.*_farmer_name$", key):
            former_name_list.append(key)
        if re.search("^.*_item_name$", key):
            item_name_list.append(key)
        if re.search("^.*_qty$", key):
            qty_list.append(key)
        if re.search("^.*_weight$", key):
            weight_list.append(key)
        if re.search("^.*_remark$", key):
            remarks_list.append(key)
        if re.search("^.*_advance_amount$", key):
            advance_amount_list.append(key)
        if re.search("^.*_arrival_goods_id$", key):
            arrival_goods_id.append(key)

    goods = []
    existing_goods_status = existing_goods_status or {}
    for index in range(0, len(former_name_list)):
        key_name = former_name_list[index]
        is_modify = "modify" in key_name

        local_id = None
        if is_modify and index < len(arrival_goods_id):
            local_id = str(request.POST[arrival_goods_id[index]]).split("_")[0]

        goods.append(
            {
                'local_id': local_id,
                'former_name': request.POST[former_name_list[index]],
                'item_name': request.POST[item_name_list[index]],
                'initial_qty': int(float(request.POST[qty_list[index]])),
                'qty': int(float(request.POST[qty_list[index]])),
                'weight': float(request.POST[weight_list[index]]),
                'remarks': request.POST[remarks_list[index]],
                'advance': float(request.POST[advance_amount_list[index]]),
                # Preserve prior settlement status for existing goods during updates.
                'patti_status': bool(existing_goods_status.get(str(local_id), False)),
            }
        )

    return goods


def add_new_arrival_entry(request):
    if request.user.is_authenticated:
        today = date.today()

        try:
            shop_detail_object = shop_metadata_repository.require_by_owner_user_id(request.user.id)
        except ValueError as error:
            messages.error(request, _shop_metadata_required_message(error))
            return render(request, 'index.html')

        if not arrival_repository.using_firebase():
            messages.error(request, _arrival_firebase_required_message())
            return home(request)

        arrival_index = {
            'arrival_entry_prefix': shop_detail_object.arrival_entry_prefix,
            'arrival_entry_counter': int(shop_detail_object.arrival_entry_counter) + 1
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
        try:
            shop_detail_object = shop_metadata_repository.require_by_owner_user_id(request.user.id)
        except ValueError as error:
            messages.error(request, _shop_metadata_required_message(error))
            return render(request, 'index.html')

        if not arrival_repository.using_firebase():
            messages.error(request, _arrival_firebase_required_message())
            return home(request)

        is_new = str(request.POST['new']) == "True"

        request_fields = list(request.POST)
        existing_goods_status = {}
        if not is_new:
            existing_record = arrival_repository.get_by_id(request.POST['id'])
            if not _belongs_to_shop(existing_record, shop_detail_object.pk):
                messages.error(request, 'Arrival record does not belong to your shop.')
                return home(request)
            if existing_record is not None:
                existing_goods_status = {
                    str(goods.local_id): bool(goods.patti_status)
                    for goods in existing_record.goods
                }

        goods_payload = _parse_arrival_goods_payload(
            request,
            request_fields,
            existing_goods_status=existing_goods_status,
        )

        if is_new:
            arrival_repository.create(
                shop_id=shop_detail_object.pk,
                arrival_id=request.POST['arrival_id'],
                gp_no=request.POST['gp_number'],
                lorry_no=request.POST['lorry_number'],
                date=getDate_from_string(request.POST['arrival_entry_date']).isoformat(),
                patti_name=request.POST['patti_name'],
                total_bags=request.POST['total_number_of_bags'],
                empty_data=False,
                goods=goods_payload,
            )
        else:
            arrival_repository.update(
                record_id=request.POST['id'],
                shop_id=shop_detail_object.pk,
                arrival_id=request.POST['arrival_id'],
                gp_no=request.POST['gp_number'],
                lorry_no=request.POST['lorry_number'],
                date=getDate_from_string(request.POST['arrival_entry_date']).isoformat(),
                patti_name=request.POST['patti_name'],
                total_bags=request.POST['total_number_of_bags'],
                empty_data=False,
                goods=goods_payload,
            )

        if is_new:
            shop_metadata_repository.increment_counter(request.user.id, 'arrival_entry_counter')

        return home(request)

    return render(request, 'index.html')


@csrf_protect
def modify_arrival(request, arrival_id):
    if request.user.is_authenticated:
        if not arrival_repository.using_firebase():
            messages.error(request, _arrival_firebase_required_message())
            return home(request)

        try:
            shop_detail_object = shop_metadata_repository.require_by_owner_user_id(request.user.id)
        except ValueError as error:
            messages.error(request, _shop_metadata_required_message(error))
            return render(request, 'index.html')

        arrival_entry_obj = arrival_repository.get_by_id(arrival_id)
        if not _belongs_to_shop(arrival_entry_obj, shop_detail_object.pk):
            messages.error(request, 'Arrival record does not belong to your shop.')
            return home(request)
        arrival_goods_objs = [] if arrival_entry_obj is None else arrival_entry_obj.goods
        today = '' if arrival_entry_obj is None else arrival_entry_obj.date

        return render(request, 'Entry/Arrival/modify_arrival_entry.html',
                      {'arrival_detail': arrival_entry_obj, 'arrival_goods_objs': arrival_goods_objs, 'new': False,
                       "today": today})
    return render(request, 'index.html')


@csrf_protect
def home(request, current_page=1):
    if request.user.is_authenticated:
        try:
            shop_detail_object = shop_metadata_repository.require_by_owner_user_id(request.user.id)
        except ValueError as error:
            messages.error(request, _shop_metadata_required_message(error))
            return render(request, 'index.html')

        if not arrival_repository.using_firebase():
            messages.error(request, _arrival_firebase_required_message())
            empty_page = Paginator([], 10).get_page(1)
            return render(request, 'Entry/Arrival/home.html',
                          {
                              'shop_details': shop_detail_object,
                              'arrival_detail': empty_page,
                              'current_page': current_page,

                          })

        arrival_entry_detail = None
        try:
            arrival_entry_detail = arrival_repository.list_non_empty_by_shop(shop_detail_object.pk)
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
