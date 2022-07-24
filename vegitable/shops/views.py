from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages, auth
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer

from .models import Misc_Entry, Sales_Bill_Entry, Shop, Arrival_Entry, Arrival_Goods
import datetime


def index(request):
    return render(request, 'index.html')


@csrf_protect
def get_authenticate(request):
    user = auth.authenticate(username=request.POST['username'], password=request.POST['password'])
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

def misc_next_page(request, page_number):
    return misc_entry(request, current_page=page_number + 1)

def misc_prev_page(request, page_number):
    if page_number > 1:
        return misc_entry(request, current_page=page_number - 1)
    else:
        return misc_entry(request)

def sales_bill_next_page(request, page_number):
    return sales_bill_entry(request, current_page=page_number + 1)

def sales_bill_prev_page(request, page_number):
    if page_number > 1:
        return sales_bill_entry(request, current_page=page_number - 1)
    else:
        return sales_bill_entry(request)
    
@csrf_protect
def home(request, page=10, current_page=1):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        arrival_entry_detail = None
        try:
            arrival_entry_detail = Arrival_Entry.objects.filter(shop=shop_detail_object).order_by('-id')[
                                   :page * current_page]
        except Exception as error:
            print(error)
            
        return render(request, 'home.html',
                      {
                          'shop_details': shop_detail_object,
                          'arrival_detail': arrival_entry_detail,
                          'current_page': current_page,

                      })
    
    return render(request, 'index.html')

def sales_bill_entry(request, page =10, current_page =1):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        sales_entry_detail = None
        try:
            sales_entry_detail = Sales_Bill_Entry.objects.filter(shop=shop_detail_object).order_by('-id')[
                                   :page * current_page]
        except Exception as error:
            print(error)
            
        return render(request, 'sales_bill_entry.html',
                      {
                        'shop_details': shop_detail_object,
                        'sales_bill_detail': sales_entry_detail,
                        'current_page': current_page
                      })
    
    return render(request, 'index.html')

def misc_entry(request, page =10, current_page =1):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        misc_entry_detail = None
        try:
            misc_entry_detail = Misc_Entry.objects.filter(shop=shop_detail_object).order_by('-id')[
                                   :page * current_page]
            
            misc_events_today = Misc_Entry.objects.filter(shop=shop_detail_object).filter(date=datetime.datetime.today()) 
            total_amount = 0
            for entry in misc_events_today:
                total_amount+=entry.amount
                print(entry.amount)
                
        except Exception as error:
            print(error)
            
        return render(request, 'misc_entry.html',
                      {
                        'shop_details': shop_detail_object,
                        'misc_detail': misc_entry_detail,
                        'current_page': current_page,
                        'total_amount':total_amount
                      })
    
    return render(request, 'index.html')


def logout(request):
    auth.logout(request)
    return render(request, 'index.html')


def add_new_arrival_entry(request):
    return render(request, 'modify_arrival_entry.html',{'NEW':True})

def add_new_misc_entry(request):
    return render(request, 'modify_misc_entry.html' , {'misc_detail': "NEW"})

def add_new_sales_bill_entry(request):
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id);
    arrival_detail_object = Arrival_Goods.objects.filter(shop=shop_detail_object)
    
    return render(request, 'modify_sales_bill_entry.html' , 
                  {'sales_bill_detail': "NEW",
                   "arrival_goods_detail":arrival_detail_object}
                  )
    
@csrf_protect
def add_misc_entry(request):
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    if len(request.POST['misc_id'])<=0:

        misc_entry_Obj = Misc_Entry(
        date=datetime.datetime.today(),
        expense_type=request.POST['expense_type'],
        amount=request.POST['amount'],
        remark=request.POST['remark'],
        shop=shop_detail_object)

    else:

        misc_entry_Obj = Misc_Entry.objects.get(id=request.POST['misc_id'])  # object to update
        misc_entry_Obj.date=datetime.datetime.today()
        misc_entry_Obj.expense_type=request.POST['expense_type']
        misc_entry_Obj.amount=request.POST['amount']
        misc_entry_Obj.remark=request.POST['remark']
        misc_entry_Obj.shop=shop_detail_object
        

    misc_entry_Obj.save()
    print(f"New arrival entry  = {misc_entry_Obj.id}")
    return misc_entry(request)

@csrf_protect
def edit_misc_entry(request,misc_id):
    misc_detail_obj = Misc_Entry.objects.get(pk=misc_id)
    return render(request, 'modify_misc_entry.html', {'misc_detail': misc_detail_obj})
    
def total_amount_misc_entry(request):
    return render(request,'misc_total_iframe.html')

@csrf_protect
def modify_arrival(request, arrival_id):
    arrival_entry_obj = Arrival_Entry.objects.get(pk=arrival_id)
    arrival_goods_objs = Arrival_Goods.objects.filter(arrival_entry=arrival_entry_obj).order_by('-id')
    return render(request, 'modify_arrival_entry.html', {'arrival_detail': arrival_entry_obj,'arrival_goods_objs':arrival_goods_objs,'NEW':False})
    
@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_arrival_goods_iteam_name(request):
    [...]
    iteam_name_list = []
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id);
    arrival_detail_object = Arrival_Goods.objects.filter(shop=shop_detail_object)
    for arrival_entry in arrival_detail_object:
        if arrival_entry.remarks == request.GET['selected_lot']:
            iteam_name_list.append(arrival_entry.iteam_name)
    data = {'iteam_name_list': iteam_name_list}
    return Response(data,status=status.HTTP_200_OK)
    
@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_arrival_goods_list(request):
    [...]
    iteam_goods_list = {}
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id);
    arrival_detail_object = Arrival_Goods.objects.filter(shop=shop_detail_object)
    for arrival_entry in arrival_detail_object:
        iteam_goods_list[arrival_entry.remarks] = arrival_entry.iteam_name
        
    data = {'iteam_goods_list': iteam_goods_list}
    return Response(data,status=status.HTTP_200_OK)

    
@csrf_protect
def add_arrival(request):
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

    if len(request.POST['arrival_id'])<=0:
        arrival_Entry_Obj = Arrival_Entry(
            gp_no=request.POST['gp_number'],
            date=datetime.datetime.today(),
            patti_name=request.POST['patti_name'],
            total_bags=request.POST['total_number_of_bags'],
            advance=request.POST['advance_amount'],
            shop=shop_detail_object)
        
    else:
        arrival_Entry_Obj = Arrival_Entry.objects.get(id=request.POST['arrival_id'])  # object to update
        arrival_Entry_Obj.gp_no=request.POST['gp_number']
        arrival_Entry_Obj.date=datetime.datetime.today()
        arrival_Entry_Obj.patti_name=request.POST['patti_name']
        arrival_Entry_Obj.total_bags=request.POST['total_number_of_bags']
        arrival_Entry_Obj.advance=request.POST['advance_amount']
        arrival_Entry_Obj.shop=shop_detail_object


    arrival_Entry_Obj.save()        
    print(f"New arrival entry  = {arrival_Entry_Obj.id}")

    if len(request.POST['arrival_id'])<=0:
        newLIst = [list(request.POST)[i:i + 5] for i in range(5, len(list(request.POST)), 5)]

        for entry in newLIst:
            arrival_Goods_obj = Arrival_Goods(
                shop=shop_detail_object,
                arrival_entry=arrival_Entry_Obj,
                former_name=request.POST[list(entry)[0]],
                iteam_name=request.POST[list(entry)[1]],
                qty=request.POST[list(entry)[2]],
                weight=request.POST[list(entry)[3]],
                remarks=request.POST[list(entry)[4]],
            )
            arrival_Goods_obj.save()
    else:
        newList = [list(request.POST)[i:i + 6] for i in range(5, len(list(request.POST)), 15)]
        
        for entry in newList:
            arrival_Goods_obj = Arrival_Goods.objects.get(id=request.POST[list(entry)[5]])  # object to update
            arrival_Goods_obj.former_name=request.POST[list(entry)[0]]
            arrival_Goods_obj.iteam_name=request.POST[list(entry)[1]]
            arrival_Goods_obj.qty=request.POST[list(entry)[2]]
            arrival_Goods_obj.weight=request.POST[list(entry)[3]]
            arrival_Goods_obj.remarks=request.POST[list(entry)[4]]
            arrival_Goods_obj.save()
            
            
        
    return home(request)

def getDate_from_string(stringDate):
    mystringDate = str(stringDate).split("-")
    return datetime.date(int(mystringDate[0]), int(mystringDate[1]), int(mystringDate[2]))
