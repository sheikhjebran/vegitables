from tokenize import Double
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages, auth
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from datetime import date
import re
from .models import Misc_Entry, Patti_entry, Sales_Bill_Entry, Sales_Bill_Iteam, Shop, Arrival_Entry, Arrival_Goods
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

def patti_list(request, page =10, current_page =1):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        patti_entry_detail = None
        try:
            patti_entry_detail = Patti_entry.objects.filter(shop=shop_detail_object).order_by('-id')[
                                   :page * current_page]
        except Exception as error:
            print(error)
            
        return render(request, 'patti.html',
                      {
                        'shop_details': shop_detail_object,
                        'patti_entry_detail': patti_entry_detail,
                        'current_page': current_page
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
    today = date.today()
    return render(request, 'modify_arrival_entry.html',{'arrival_detail':"NEW","today":today})

def add_new_misc_entry(request):
    return render(request, 'modify_misc_entry.html' , {'misc_detail': "NEW"})

def add_new_patti_entry(request):
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    
    today = date.today()
    print("Today's date:", today)
    
    return render(request, 'modify_patti_entry.html' , 
                  {'patti_bill_detail': "NEW","today":today}
                  )
    
def add_new_sales_bill_entry(request):
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    arrival_detail_object = Arrival_Goods.objects.filter(shop=shop_detail_object).filter(qty__gte = 0)
    
    today = date.today()
    print("Today's date:", today)
    
    return render(request, 'modify_sales_bill_entry.html' , 
                  {'sales_bill_detail': "NEW",
                   "arrival_goods_detail":arrival_detail_object,"today":today}
                  )
    
def getDate_from_string(stringDate):
    mystringDate = str(stringDate).split("-")
    return datetime.date(int(mystringDate[0]), int(mystringDate[1]), int(mystringDate[2]))

def modify_sales_bill_entry(request):
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    if len(request.POST['sales_bill_id'])<=0:
        sales_bill_entry_Obj = Sales_Bill_Entry(
        
        payment_type=request.POST['payment_mode'],
        customer_name=request.POST['sales_entry_customer_name'],
        date=getDate_from_string(request.POST['sales_entry_date']),
        shop=shop_detail_object,
        rmc=request.POST['rmc'],
        commission=request.POST['comission'],
        cooli=request.POST['cooli'],
        total_amount=request.POST['total_amount']
        )
    else:
        sales_bill_entry_Obj = Sales_Bill_Entry.objects.get(id=request.POST['sales_bill_id'])

    
    sales_bill_entry_Obj.save()
    print(f"New Sales Bill entry  = {sales_bill_entry_Obj.id}")

    add_sales_bill_iteam(request, list(request.POST),sales_bill_entry_Obj)
    return sales_bill_entry(request)

def add_sales_bill_iteam(request,request_list, sales):
    lot_number_list = []
    bags_list = []
    net_weight_list = []
    rates_list = []
    amount_list = []
    iteam_name_list = []

    for i in request_list:

        lot_number_regrex = re.search("^.*_lot_number$", i)
        if lot_number_regrex:
            lot_number_list.append(i)
        
        iteam_name_regrex = re.search("^.*_iteam_name$", i)
        if iteam_name_regrex:
            iteam_name_list.append(i)
        
        bag_regrex = re.search("^.*_bags$", i)
        if bag_regrex:
            bags_list.append(i)
        
        net_weight_regrex = re.search("^.*_net_weight$", i)
        if net_weight_regrex:
            net_weight_list.append(i)
            
        rates_regrex = re.search("^.*_rates$", i)
        if rates_regrex:
            rates_list.append(i)

        amount_regrex = re.search("^.*_amount$", i)
        if amount_regrex:
            amount_list.append(i)
        
    for i in range(0, len(lot_number_list)):
        sales_bill_entry_Obj = Sales_Bill_Iteam(
            iteam_name= request.POST[iteam_name_list[i]],
            lot_number=request.POST[lot_number_list[i]],
            bags=request.POST[bags_list[i]],
            net_weight=request.POST[net_weight_list[i]],
            rates=request.POST[rates_list[i]],
            amount=request.POST[amount_list[i]],
            Sales_Bill_Entry = sales
        )

        sales_bill_entry_Obj.save()
        print(f"New Sales Bill Iteam  = {sales_bill_entry_Obj.id}")


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
    
    today = arrival_entry_obj.date
    
    return render(request, 'modify_arrival_entry.html', {'arrival_detail': arrival_entry_obj,'arrival_goods_objs':arrival_goods_objs,'NEW':False,"today":today})
    
@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_arrival_goods_iteam_name(request):
    [...]
    iteam_name_list = []
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
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
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
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
            date= getDate_from_string(request.POST['arrival_entry_date']),
            patti_name=request.POST['patti_name'],
            total_bags=request.POST['total_number_of_bags'],
            lorry_no = request.POST['lorry_number'],
            shop=shop_detail_object)
        
    else:
        arrival_Entry_Obj = Arrival_Entry.objects.get(id=request.POST['arrival_id'])  # object to update
        arrival_Entry_Obj.gp_no=request.POST['gp_number']
        arrival_Entry_Obj.date=getDate_from_string(request.POST['arrival_entry_date'])
        arrival_Entry_Obj.patti_name=request.POST['patti_name']
        arrival_Entry_Obj.total_bags=request.POST['total_number_of_bags']
        arrival_Entry_Obj.lorry_no = request.POST['lorry_number']
        arrival_Entry_Obj.shop=shop_detail_object


    arrival_Entry_Obj.save()        
    print(f"New arrival entry  = {arrival_Entry_Obj.id}")
        
    add_arrival_goods_iteam(request, list(request.POST), arrival_Entry_Obj ,shop_detail_object)
    
    return home(request)


def add_arrival_goods_iteam(request, request_list,arrival,shop_obj):
    former_name_list = []
    iteam_name_list = []
    qty_list = []
    weight_list = []
    remarks_list = []
    arrival_goods_id = []
    advance_amount_list = []
    
    for i in request_list:
        former_name_regrex = re.search("^.*_farmer_name$", i)
        if former_name_regrex:
            former_name_list.append(i)
    
        iteam_name_regrex = re.search("^.*_iteam_name$", i)
        if iteam_name_regrex:
            iteam_name_list.append(i)
    
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
        if "modify" in iteam_name_list[i]:
            local_id = request.POST[arrival_goods_id[i]].split("_")[0]
            # object to update
            arrival_Goods_obj = Arrival_Goods.objects.get(id= int(local_id))
            arrival_Goods_obj.iteam_name = request.POST[iteam_name_list[i]]
            arrival_Goods_obj.former_name = request.POST[former_name_list[i]]
            arrival_Goods_obj.qty = request.POST[qty_list[i]]
            arrival_Goods_obj.advance= request.POST[advance_amount_list[i]]
            arrival_Goods_obj.weight=request.POST[weight_list[i]]
            arrival_Goods_obj.remarks=request.POST[remarks_list[i]]
            
            arrival_Goods_obj.save()
            print(f"Update Arrival Goods Iteam  = {arrival_Goods_obj.id}") 
            
        else: 
            
            arrival_Goods_obj = Arrival_Goods(
                iteam_name = request.POST[iteam_name_list[i]],
                shop = shop_obj,
                arrival_entry = arrival,
                former_name = request.POST[former_name_list[i]],
                advance = request.POST[advance_amount_list[i]],
                qty = request.POST[qty_list[i]],
                weight=request.POST[weight_list[i]],
                remarks=request.POST[remarks_list[i]],
            )

            arrival_Goods_obj.save()
            print(f"New Arrival Goods Iteam  = {arrival_Goods_obj.id}")
    
    
    

def getDate_from_string(stringDate):
    mystringDate = str(stringDate).split("-")
    return datetime.date(int(mystringDate[0]), int(mystringDate[1]), int(mystringDate[2]))


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_lorry_number_for_date(request,lorry_date):
    [...]
    lorry_number_list = []
    lorry_date = getDate_from_string(lorry_date)
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    
    arrival_detail_object = Arrival_Entry.objects.filter(shop=shop_detail_object)
    for arrival_entry in arrival_detail_object:
        if arrival_entry.date == lorry_date:
            lorry_number_list.append(arrival_entry.lorry_no)
        
    data = {'lorry_number_list': lorry_number_list}
    return Response(data,status=status.HTTP_200_OK)

@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_all_farmer_name(request):
    [...]
    farmer_name_list = []
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    
    lorry_number = request.GET['lorry_number']
    patti_date = getDate_from_string(request.GET['patti_date'])
    
    
    arrival_detail_object = Arrival_Entry.objects.get(
        shop=shop_detail_object,
        lorry_no = lorry_number,
        date = patti_date )
    
    arrival_good_object = Arrival_Goods.objects.filter(
        shop = shop_detail_object,
        arrival_entry = arrival_detail_object,
    )
    
    for arrival_goods_entry in arrival_good_object:
        farmer_name_list.append(arrival_goods_entry.former_name)
        
    data = {'farmer_list': farmer_name_list}
    return Response(data,status=status.HTTP_200_OK)

