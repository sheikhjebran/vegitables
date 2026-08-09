from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.decorators import api_view

from .. import utility
from ..repositories.customer_ledger_repository import CustomerLedgerRepository
from ..repositories.shop_metadata_repository import ShopMetadataRepository


customer_ledger_repository = CustomerLedgerRepository()
shop_metadata_repository = ShopMetadataRepository()


def _load_shop_metadata(user_id):
    return shop_metadata_repository.require_by_owner_user_id(user_id)


def _belongs_to_shop(record, shop_id):
    return record is not None and int(record.shop_id) == int(shop_id)

@csrf_protect
def customer_ledger(request, current_page=1, customer_ledger_entry=None, message=None):
    if request.user.is_authenticated:
        if customer_ledger_entry is None:
            customer_ledger_entry = {
                "name": "",
                "contact": "",
                "address": "",
                "id": None
            }
        items_per_page = 10
        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)
        request.session['form_token'] = utility.generate_unique_number()
        customer_ledger_list = customer_ledger_repository.list_by_shop(shop_detail_object.pk)
        paginator = Paginator(customer_ledger_list, items_per_page)
        customer_ledger_list = paginator.get_page(current_page)
        return render(request, 'Ledger/customer_ledger.html',
                      {'customer_ledger_list': customer_ledger_list,
                       'current_page': current_page,
                       'customer_ledger': customer_ledger_entry,
                       'message':message})
    return render(request, 'index.html')

@csrf_protect
def add_customer_ledger(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            if request.POST.get('form_token') == str(request.session.get('form_token')):
                # Remove the token from the session
                del request.session['form_token']
                try:
                    shop = _load_shop_metadata(request.user.id)
                except ValueError as error:
                    return JsonResponse({'error': str(error)}, status=400)
                if request.POST['customer_ledger_id'] == "None":
                    if not customer_ledger_repository.exists_by_contact(shop_id=shop.pk, contact=request.POST['contact']):
                        customer_ledger_repository.create(
                            shop_id=shop.pk,
                            name=request.POST['name'],
                            contact=request.POST['contact'],
                            address=request.POST['address'],
                        )
                    else:
                        return customer_ledger(request, message="Customer Entry already exists")
                else:
                    existing_record = customer_ledger_repository.get_by_id(request.POST['customer_ledger_id'])
                    if not _belongs_to_shop(existing_record, shop.pk):
                        return JsonResponse({'error': 'Customer ledger record does not belong to your shop.'}, status=403)
                    customer_ledger_repository.update(
                        record_id=request.POST['customer_ledger_id'],
                        shop_id=shop.pk,
                        name=request.POST['name'],
                        contact=request.POST['contact'],
                        address=request.POST['address'],
                    )
        request.session['form_token'] = utility.generate_unique_number()
        return customer_ledger(request)

    return render(request, 'index.html')

@api_view(['GET'])
def search_customer_ledger(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        shop_detail_object = _load_shop_metadata(request.user.id)
    except ValueError as error:
        return JsonResponse({'error': str(error)}, status=400)
    customerLedgerObject = customer_ledger_repository.search(
        shop_id=shop_detail_object.pk,
        search_text=request.GET['search_text'],
    )
    response = []
    for customer in customerLedgerObject:
        customer_dict = {
            'id': customer.id,
            'name': customer.name,
            'contact': customer.contact,
            'address': customer.address
        }
        response.append(customer_dict)
    if len(response) >= 1:
        return JsonResponse(data={'FOUND': True, 'result': response}, status=status.HTTP_200_OK)
    else:
        return JsonResponse(data={'FOUND': False}, status=status.HTTP_404_NOT_FOUND)

def default_customer_ledger(request, current_page=1, customer_ledger_entry=None):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.user.is_authenticated:
        if customer_ledger_entry is None:
            customer_ledger_entry = {
                "name": "",
                "contact": "",
                "address": "",
                "id": None
            }
        items_per_page = 10
        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)
        request.session['form_token'] = utility.generate_unique_number()
        customer_ledger_list = customer_ledger_repository.list_by_shop(shop_detail_object.pk)
        paginator = Paginator(customer_ledger_list, items_per_page)
        customer_ledger_list = paginator.get_page(current_page)
        response = [
            {
                'id': customer.id,
                'name': customer.name,
                'contact': customer.contact,
                'address': customer.address
            }
            for customer in customer_ledger_list
        ]
        if len(response) >= 1:
            return JsonResponse(data={'FOUND': True, 'result': response}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(data={'FOUND': False}, status=status.HTTP_404_NOT_FOUND)

def customer_ledger_next_page(request, page_number):
    return customer_ledger(request, current_page=page_number + 1)


def customer_ledger_prev_page(request, page_number):
    if page_number > 1:
        return customer_ledger(request, current_page=page_number - 1)
    else:
        return customer_ledger(request)

@csrf_protect
def edit_customer_ledger(request, customer_id):
    if request.user.is_authenticated:
        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)
        customer_ledger_detail = customer_ledger_repository.get_by_id(customer_id)
        if not _belongs_to_shop(customer_ledger_detail, shop_detail_object.pk):
            return JsonResponse({'error': 'Customer ledger record does not belong to your shop.'}, status=403)
        return customer_ledger(request, customer_ledger_entry=customer_ledger_detail)
    return render(request, 'index.html')


@csrf_protect
def delete_customer_ledger(request, customer_id):
    if request.user.is_authenticated:
        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)
        customer_ledger_detail = customer_ledger_repository.get_by_id(customer_id)
        if not _belongs_to_shop(customer_ledger_detail, shop_detail_object.pk):
            return JsonResponse({'error': 'Customer ledger record does not belong to your shop.'}, status=403)
        customer_ledger_repository.delete(customer_id)
        return customer_ledger(request)
    return render(request, 'index.html')
