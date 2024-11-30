from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.decorators import api_view

from .. import utility
from ..models import Shop, FarmerLedger


@csrf_protect
def farmer_ledger(request, current_page=1, farmer_ledger_entry=None):
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
        farmer_ledger_list = FarmerLedger.objects.filter(
            shop=shop_detail_object).order_by('-id')
        paginator = Paginator(farmer_ledger_list, items_per_page)
        farmer_ledger_list = paginator.get_page(current_page)
        return render(request, 'Ledger/farmer_ledger.html',
                      {'farmer_ledger_list': farmer_ledger_list,
                       'current_page': current_page,
                       'farmer_ledger': farmer_ledger_entry})
    return render(request, 'index.html')

@csrf_protect
def add_farmer_ledger(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            if request.POST.get('form_token') == str(request.session.get('form_token')):
                del request.session['form_token']
                if request.POST['farmer_ledger_id'] == "None" or len(request.POST['farmer_ledger_id']) == 0:
                    if not FarmerLedger.objects.filter(contact=request.POST['contact']).exists():
                        farmer_ledger_obj = FarmerLedger(
                            name=request.POST['name'],
                            contact=request.POST['contact'],
                            place=request.POST['place'],
                            shop=Shop.objects.get(shop_owner=request.user.id)
                        )
                        farmer_ledger_obj.save()
                else:
                    farmer_ledger_obj = FarmerLedger.objects.get(
                        id=request.POST['farmer_ledger_id'])
                    farmer_ledger_obj.name = request.POST['name']
                    farmer_ledger_obj.contact = request.POST['contact']
                    farmer_ledger_obj.place = request.POST['place']
                    farmer_ledger_obj.shop = Shop.objects.get(
                        shop_owner=request.user.id)
                    farmer_ledger_obj.save()
        request.session['form_token'] = utility.generate_unique_number()
        return farmer_ledger(request)

    return render(request, 'index.html')

@api_view(['GET'])
def search_farmer_ledger(request):
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

    search_text = request.GET.get('search_text', '').strip()

    if search_text:
        farmer_ledger_objects = FarmerLedger.objects.filter(shop=shop_detail_object).filter(
            name__icontains=search_text) | FarmerLedger.objects.filter(shop=shop_detail_object).filter(
            contact__icontains=search_text) | FarmerLedger.objects.filter(shop=shop_detail_object).filter(
            place__icontains=search_text)
    else:
        farmer_ledger_objects = FarmerLedger.objects.filter(
            shop=shop_detail_object)

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
        farmer_ledger_list = FarmerLedger.objects.filter(
            shop=shop_detail_object)

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
        farmer_ledger_detail = FarmerLedger.objects.get(pk=farmer_id)
        return farmer_ledger(request, farmer_ledger_entry=farmer_ledger_detail)
    return render(request, 'index.html')


@csrf_protect
def delete_farmer_ledger(request, farmer_id):
    if request.user.is_authenticated:
        farmer_ledger_detail = FarmerLedger.objects.get(pk=farmer_id)
        farmer_ledger_detail.delete()
        return farmer_ledger(request)
    return render(request, 'index.html')
