from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.decorators import api_view

from .. import utility
from ..models import Shop, FarmerLedger
from ..repositories.farmer_ledger_repository import FarmerLedgerRepository


farmer_ledger_repository = FarmerLedgerRepository()


@csrf_protect
def farmer_ledger(request, current_page=1, farmer_ledger_entry=None, message=None):
    if request.user.is_authenticated:
        if farmer_ledger_entry is None:
            farmer_ledger_entry = {
                "name": "",
                "contact": "",
                "place": "",
                "id": None
            }
        items_per_page = 10
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        request.session['form_token'] = utility.generate_unique_number()
        farmer_ledger_list = farmer_ledger_repository.list_by_shop(shop_detail_object.pk)
        paginator = Paginator(farmer_ledger_list, items_per_page)
        farmer_ledger_list = paginator.get_page(current_page)
        return render(request, 'Ledger/farmer_ledger.html',
                      {'farmer_ledger_list': farmer_ledger_list,
                       'current_page': current_page,
                       'farmer_ledger': farmer_ledger_entry,
                       'message':message})
    return render(request, 'index.html')


@csrf_protect
def add_farmer_ledger(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            if request.POST.get('form_token') == str(request.session.get('form_token')):
                del request.session['form_token']
                shop = Shop.objects.get(shop_owner=request.user.id)
                if request.POST['farmer_ledger_id'] == "None" or len(request.POST['farmer_ledger_id']) == 0:
                    if not farmer_ledger_repository.exists_by_contact(request.POST['contact']):
                        farmer_ledger_repository.create(
                            shop_id=shop.pk,
                            name=request.POST['name'],
                            contact=request.POST['contact'],
                            place=request.POST['place'],
                        )
                    else:
                        return farmer_ledger(request, message="Farmer Entry already exists")
                else:
                    farmer_ledger_repository.update(
                        record_id=request.POST['farmer_ledger_id'],
                        shop_id=shop.pk,
                        name=request.POST['name'],
                        contact=request.POST['contact'],
                        place=request.POST['place'],
                    )
        request.session['form_token'] = utility.generate_unique_number()
        return farmer_ledger(request)

    return render(request, 'index.html')


@api_view(['GET'])
def search_farmer_ledger(request):
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

    search_text = request.GET.get('search_text', '').strip()

    if search_text:
        farmer_ledger_objects = farmer_ledger_repository.search(
            shop_id=shop_detail_object.pk,
            search_text=search_text,
        )
    else:
        farmer_ledger_objects = farmer_ledger_repository.list_by_shop(shop_detail_object.pk)

    response = [
        {
            'id': farmer.id,
            'name': farmer.name,
            'contact': farmer.contact,
            'place': farmer.place
        }
        for farmer in farmer_ledger_objects
    ]

    if response:
        return JsonResponse(data={'FOUND': True, 'result': response}, status=status.HTTP_200_OK)
    else:
        return JsonResponse(data={'FOUND': False}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def default_farmer_ledger(request):
    if request.user.is_authenticated:
        items_per_page = 10
        current_page = 1

        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        request.session['form_token'] = utility.generate_unique_number()
        farmer_ledger_list = farmer_ledger_repository.list_by_shop(shop_detail_object.pk)

        paginator = Paginator(farmer_ledger_list, items_per_page)
        farmer_ledger_list = paginator.get_page(current_page)

        response = [
            {
                'id': farmer.id,
                'name': farmer.name,
                'contact': farmer.contact,
                'place': farmer.place
            }
            for farmer in farmer_ledger_list
        ]

        if response:
            return JsonResponse(data={'FOUND': True, 'result': response}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(data={'FOUND': False}, status=status.HTTP_404_NOT_FOUND)


def farmer_ledger_prev_page(request, page_number):
    if page_number > 1:
        return farmer_ledger(request, current_page=page_number - 1)
    else:
        return farmer_ledger(request)


def farmer_ledger_next_page(request, page_number):
    return farmer_ledger(request, current_page=page_number + 1)


@csrf_protect
def edit_farmer_ledger(request, farmer_id):
    if request.user.is_authenticated:
        farmer_ledger_detail = farmer_ledger_repository.get_by_id(farmer_id)
        return farmer_ledger(request, farmer_ledger_entry=farmer_ledger_detail)
    return render(request, 'index.html')


@csrf_protect
def delete_farmer_ledger(request, farmer_id):
    if request.user.is_authenticated:
        farmer_ledger_repository.delete(farmer_id)
        return farmer_ledger(request)
    return render(request, 'index.html')
