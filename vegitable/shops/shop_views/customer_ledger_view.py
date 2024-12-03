from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.decorators import api_view

from .. import utility
from ..models import Shop, CustomerLedger

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
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        request.session['form_token'] = utility.generate_unique_number()
        customer_ledger_list = CustomerLedger.objects.filter(
            shop=shop_detail_object).order_by('-id')
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
                if request.POST['customer_ledger_id'] == "None":
                    if not CustomerLedger.objects.filter(contact=request.POST['contact']).exists():
                        customer_ledger_obj = CustomerLedger(
                            name=request.POST['name'],
                            contact=request.POST['contact'],
                            address=request.POST['address'],
                            shop=Shop.objects.get(shop_owner=request.user.id)
                        )
                        customer_ledger_obj.save()
                    else:
                        return customer_ledger(request, message="Customer Entry already exists")
                else:
                    customer_ledger_obj = CustomerLedger.objects.get(
                        id=request.POST['customer_ledger_id'])
                    customer_ledger_obj.name = request.POST['name']
                    customer_ledger_obj.contact = request.POST['contact']
                    customer_ledger_obj.address = request.POST['address']
                    customer_ledger_obj.shop = Shop.objects.get(
                        shop_owner=request.user.id)
                    customer_ledger_obj.save()
        request.session['form_token'] = utility.generate_unique_number()
        return customer_ledger(request)

    return render(request, 'index.html')

@api_view(['GET'])
def search_customer_ledger(request):
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    customerLedgerObject = CustomerLedger.objects.filter(shop=shop_detail_object).filter(
        name__icontains=request.GET['search_text']) | CustomerLedger.objects.filter(shop=shop_detail_object).filter(
        contact__icontains=request.GET['search_text']) | CustomerLedger.objects.filter(shop=shop_detail_object).filter(
        address__icontains=request.GET['search_text'])
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
    if request.user.is_authenticated:
        if customer_ledger_entry is None:
            customer_ledger_entry = {
                "name": "",
                "contact": "",
                "address": "",
                "id": None
            }
        items_per_page = 10
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        request.session['form_token'] = utility.generate_unique_number()
        customer_ledger_list = CustomerLedger.objects.filter(
            shop=shop_detail_object).order_by('-id')
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
        customer_ledger_detail = CustomerLedger.objects.get(pk=customer_id)
        return customer_ledger(request, customer_ledger_entry=customer_ledger_detail)
    return render(request, 'index.html')


@csrf_protect
def delete_customer_ledger(request, customer_id):
    if request.user.is_authenticated:
        customer_ledger_detail = CustomerLedger.objects.get(pk=customer_id)
        customer_ledger_detail.delete()
        return customer_ledger(request)
    return render(request, 'index.html')
