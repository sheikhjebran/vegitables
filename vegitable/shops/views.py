from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages, auth
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from datetime import date
import re
from django.db import models
from django.core.paginator import Paginator

from . import utility
from .models import Expenditure_Entry, Patti_entry, Patti_entry_list, Sales_Bill_Entry, Sales_Bill_Iteam, Shop, \
    Arrival_Entry, \
    Arrival_Goods, CustomerLedger, FarmerLedger
import datetime
# Report import
from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter


def index(request):
    return render(request, 'index.html')


def getDate_from_string(stringDate):
    mystringDate = str(stringDate).split("-")
    return datetime.date(int(mystringDate[0]), int(mystringDate[1]), int(mystringDate[2]))


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


def customer_ledger_next_page(request, page_number):
    return customer_ledger(request, current_page=page_number + 1)


def farmer_ledger_next_page(request, page_number):
    return farmer_ledger(request, current_page=page_number + 1)


def customer_ledger_prev_page(request, page_number):
    if page_number > 1:
        return customer_ledger(request, current_page=page_number - 1)
    else:
        return customer_ledger(request)


def farmer_ledger_prev_page(request, page_number):
    if page_number > 1:
        return farmer_ledger(request, current_page=page_number - 1)
    else:
        return farmer_ledger(request)


def inventory_next_page(request, page_number):
    return inventory(request, current_page=page_number + 1)


def inventory_prev_page(request, page_number):
    if page_number > 1:
        return inventory(request, current_page=page_number - 1)
    else:
        return inventory(request)


def expenditure_next_page(request, page_number):
    return expenditure_entry(request, current_page=page_number + 1)


def expenditure_prev_page(request, page_number):
    if page_number > 1:
        return expenditure_entry(request, current_page=page_number - 1)
    else:
        return expenditure_entry(request)


def sales_bill_next_page(request, page_number):
    return sales_bill_entry(request, current_page=page_number + 1)


def sales_bill_prev_page(request, page_number):
    if page_number > 1:
        return sales_bill_entry(request, current_page=page_number - 1)
    else:
        return sales_bill_entry(request)


@csrf_protect
def home(request, current_page=1):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        arrival_entry_detail = None
        try:

            arrival_entry_detail = Arrival_Entry.objects.filter(shop=shop_detail_object).filter(
                Empty_data=False).order_by('-id')
            items_per_page = 10
            paginator = Paginator(arrival_entry_detail, items_per_page)
            arrival_entry_detail = paginator.get_page(current_page)

        except Exception as error:
            print(error)

        return render(request, 'home.html',
                      {
                          'shop_details': shop_detail_object,
                          'arrival_detail': arrival_entry_detail,
                          'current_page': current_page,

                      })

    return render(request, 'index.html')


@csrf_protect
def customer_ledger(request, current_page=1):
    if request.user.is_authenticated:
        items_per_page = 10
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        request.session['form_token'] = utility.generate_unique_number()
        customer_ledger_list = CustomerLedger.objects.filter(shop=shop_detail_object).order_by('-id')
        paginator = Paginator(customer_ledger_list, items_per_page)
        customer_ledger_list = paginator.get_page(current_page)
        return render(request, 'customer_ledger.html',
                      {'customer_ledger_list': customer_ledger_list, 'current_page': current_page})
    return render(request, 'index.html')


@csrf_protect
def farmer_ledger(request, current_page=1):
    if request.user.is_authenticated:
        items_per_page = 10

        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        request.session['form_token'] = utility.generate_unique_number()
        farmer_ledger_list = FarmerLedger.objects.filter(shop=shop_detail_object)

        paginator = Paginator(farmer_ledger_list, items_per_page)
        farmer_ledger_list = paginator.get_page(current_page)

        return render(request, 'farmer_ledger.html',
                      {'farmer_ledger_list': farmer_ledger_list,
                       'current_page': current_page})
    return render(request, 'index.html')


def inventory(request, current_page=1):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        entries = Arrival_Entry.objects.filter(shop_id=shop_detail_object).values('date') \
            .annotate(
            qty=models.F('arrival_goods__qty'),
            remarks=models.F('arrival_goods__remarks'),
            initial_qty=models.F('arrival_goods__initial_qty'),
            sold_qty=models.F('arrival_goods__initial_qty') - models.F('arrival_goods__qty'),
            iteam_name=models.F('arrival_goods__iteam_name')
        ).filter(arrival_goods__shop_id=shop_detail_object)

        items_per_page = 10
        paginator = Paginator(entries, items_per_page)
        entries = paginator.get_page(current_page)

        return render(request, 'inventory.html', {'entries_list': entries,
                                                  'current_page': current_page})
    return render(request, 'index.html')


@csrf_protect
def add_customer_ledger(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            if request.POST.get('form_token') == str(request.session.get('form_token')):
                del request.session['form_token']  # Remove the token from the session

                customer_ledger_obj = CustomerLedger(
                    name=request.POST['name'],
                    contact=request.POST['contact'],
                    address=request.POST['address'],
                    shop=Shop.objects.get(shop_owner=request.user.id)
                )
                customer_ledger_obj.save()
        request.session['form_token'] = utility.generate_unique_number()
        return customer_ledger(request)

    return render(request, 'index.html')


@csrf_protect
def add_farmer_ledger(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            if request.POST.get('form_token') == str(request.session.get('form_token')):
                del request.session['form_token']  # Remove the token from the session
                farmer_ledger_obj = FarmerLedger(
                    name=request.POST['name'],
                    contact=request.POST['contact'],
                    place=request.POST['place'],
                    shop=Shop.objects.get(shop_owner=request.user.id)
                )
                farmer_ledger_obj.save()

        request.session['form_token'] = utility.generate_unique_number()
        return farmer_ledger(request)
    return render(request, 'index.html')


def patti_list(request, current_page=1):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        patti_entry_detail = None
        try:
            patti_entry_detail = Patti_entry.objects.filter(shop=shop_detail_object).filter(Empty_data=False).order_by(
                '-id')
            items_per_page = 10
            paginator = Paginator(patti_entry_detail, items_per_page)
            patti_entry_detail = paginator.get_page(current_page)
        except Exception as error:
            print(error)

        return render(request, 'patti.html',
                      {
                          'shop_details': shop_detail_object,
                          'patti_entry_detail': patti_entry_detail,
                          'current_page': current_page
                      })

    return render(request, 'index.html')


def sales_bill_entry(request, current_page=1):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

        sales_entry_detail = None
        try:
            sales_entry_detail = Sales_Bill_Entry.objects.filter(shop=shop_detail_object).filter(
                Empty_data=False).order_by('-id')
            items_per_page = 10
            paginator = Paginator(sales_entry_detail, items_per_page)
            sales_entry_detail = paginator.get_page(current_page)

        except Exception as error:
            print(error)

        return render(request, 'sales_bill_entry.html',
                      {
                          'shop_details': shop_detail_object,
                          'sales_bill_detail': sales_entry_detail,
                          'current_page': current_page
                      })

    return render(request, 'index.html')


def profile(request):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

        return render(request, 'profile.html',
                      {
                          'shop_details': shop_detail_object,
                      })
    else:
        return render(request, 'index.html')


def expenditure_entry(request, current_page=1, expenditure_detail=None):
    total_amount = 0
    expenditure_events_today = None
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        try:

            expenditure_events_today = Expenditure_Entry.objects.filter(shop=shop_detail_object).filter(
                date=datetime.datetime.today())
            total_amount = 0
            for entry in expenditure_events_today:
                total_amount += entry.amount

            items_per_page = 10
            if len(expenditure_events_today) > 0:
                paginator = Paginator(expenditure_events_today, items_per_page)
                expenditure_events_today = paginator.get_page(current_page)

        except Exception as error:
            print(error)
        if expenditure_detail is None:
            expenditure_detail = {
                "id": None,
                "expense_type": "Cash",
                "amount": 0,
                "remark": "",
                "shop": shop_detail_object
            }
        return render(request, 'Entry/Expense/expenditure.html',
                      {
                          'shop_details': shop_detail_object,
                          'expenditure_detail': expenditure_events_today,
                          'current_page': current_page,
                          'total_amount': total_amount,
                          'expenditure': expenditure_detail,
                      })

    return render(request, 'index.html')


def logout(request):
    auth.logout(request)
    return render(request, 'index.html')


def add_new_arrival_entry(request):
    if request.user.is_authenticated:
        today = date.today()
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        # arrival_Entry_Obj = Arrival_Entry(
        #     gp_no="",
        #     date=getDate_from_string(today),
        #     patti_name="",
        #     total_bags=0,
        #     lorry_no="",
        #     shop=shop_detail_object
        # )
        # arrival_Entry_Obj.save()

        return render(request, 'modify_arrival_entry.html', {
            # "arrival_detail": arrival_Entry_Obj,
            "today": today,
            "NEW": True
        })
    return render(request, 'index.html')


def add_new_expenditure_entry(request):
    if request.user.is_authenticated:
        return render(request, 'modify_expenditure_entry.html', {'expenditure_detail': "NEW"})
    return render(request, 'index.html')


def add_new_patti_entry(request):
    if request.user.is_authenticated:
        today = date.today()
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

        patti_bill_detail = Patti_entry(
            lorry_no="",
            date=today,
            advance=0,
            farmer_name="",
            total_weight=0,
            hamali=0,
            net_amount=0,
            shop=shop_detail_object,
        )
        patti_bill_detail.save()

        return render(request, 'modify_patti_entry.html',
                      {'patti_bill_detail': patti_bill_detail,
                       "today": today,
                       "NEW": True}
                      )
    return render(request, 'index.html')


def navigate_to_add_sales_bill_entry(request):
    if request.user.is_authenticated:
        today = date.today()

        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

        sales_obj = Sales_Bill_Entry(
            payment_type="",
            customer_name="",
            date=getDate_from_string(today),
            shop=shop_detail_object,
            rmc=0,
            commission=0,
            cooli=0,
            total_amount=0
        )
        sales_obj.save()

        arrival_detail_object = Arrival_Goods.objects.filter(shop=shop_detail_object, qty__gte=1)

        return render(request, 'modify_sales_bill_entry.html', {
            'sales_bill_detail': True,
            'sales_obj': sales_obj,
            'NEW': True,
            "arrival_goods_detail": arrival_detail_object,
            "today": today
        })
    return render(request, 'index.html')


def modify_sales_bill_entry(request):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        if len(request.POST['sales_bill_id']) <= 0:
            sales_bill_entry_Obj = Sales_Bill_Entry(
                payment_type=request.POST['payment_mode'],
                customer_name=request.POST['sales_entry_customer_name'],
                date=getDate_from_string(request.POST['sales_entry_date']),
                shop=shop_detail_object,
                rmc=request.POST['rmc'],
                commission=request.POST['comission'],
                cooli=request.POST['cooli'],
                total_amount=round(float(request.POST['total_amount']), 2),
                Empty_data=False
            )
        else:
            sales_bill_entry_Obj = Sales_Bill_Entry.objects.get(id=request.POST['sales_bill_id'])
            sales_bill_entry_Obj.payment_type = request.POST['payment_mode']
            sales_bill_entry_Obj.customer_name = request.POST['sales_entry_customer_name']
            sales_bill_entry_Obj.date = getDate_from_string(request.POST['sales_entry_date'])
            sales_bill_entry_Obj.shop = shop_detail_object
            sales_bill_entry_Obj.rmc = request.POST['rmc']
            sales_bill_entry_Obj.commission = request.POST['comission']
            sales_bill_entry_Obj.cooli = request.POST['cooli']
            sales_bill_entry_Obj.total_amount = round(float(request.POST['total_amount']), 2)
            sales_bill_entry_Obj.Empty_data = False

        sales_bill_entry_Obj.save()
        print(f"New Sales Bill entry  = {sales_bill_entry_Obj.id}")

        add_sales_bill_iteam(request, list(request.POST), sales_bill_entry_Obj)
        return sales_bill_entry(request)
    return render(request, 'index.html')


def add_sales_bill_iteam(request, request_list, sales):
    if request.user.is_authenticated:
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
            arrival_goods_entry_Obj = Arrival_Goods.objects.get(id=request.POST[lot_number_list[i]])

            arrival_goods_entry_Obj.qty = int(arrival_goods_entry_Obj.qty) - int(request.POST[bags_list[i]])
            arrival_goods_entry_Obj.save()

            sales_bill_entry_Obj = Sales_Bill_Iteam(
                iteam_name=request.POST[iteam_name_list[i]],
                arrival_goods=arrival_goods_entry_Obj,
                bags=request.POST[bags_list[i]],
                net_weight=request.POST[net_weight_list[i]],
                rates=request.POST[rates_list[i]],
                amount=request.POST[amount_list[i]],
                Sales_Bill_Entry=sales
            )

            sales_bill_entry_Obj.save()

            print(f"New Sales Bill Iteam  = {sales_bill_entry_Obj.id}")
    return render(request, 'index.html')


@csrf_protect
def add_expenditure_entry(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            if request.POST.get('form_token') == str(request.session.get('form_token')):
                del request.session['form_token']  # Remove the token from the session
                shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
                if request.POST['expenditure_id'] == "None":

                    expenditure_entry_Obj = Expenditure_Entry(
                        date=datetime.datetime.today(),
                        expense_type=str(request.POST['expense_type']).upper(),
                        amount=request.POST['expense_amount'],
                        remark=request.POST['expense_remark'],
                        shop=shop_detail_object)
                else:
                    expenditure_entry_Obj = Expenditure_Entry.objects.get(
                        id=request.POST['expenditure_id'])  # object to update
                    expenditure_entry_Obj.date = datetime.datetime.today()
                    expenditure_entry_Obj.expense_type = str(request.POST['expense_type']).upper()
                    expenditure_entry_Obj.amount = request.POST['expense_amount']
                    expenditure_entry_Obj.remark = request.POST['expense_remark']
                    expenditure_entry_Obj.shop = shop_detail_object

                expenditure_entry_Obj.save()
                print(f"New arrival entry  = {expenditure_entry_Obj.id}")
            request.session['form_token'] = utility.generate_unique_number()
            return expenditure_entry(request)

    return render(request, 'index.html')


@csrf_protect
def edit_expense(request, expenditure_id):
    if request.user.is_authenticated:
        expenditure_entry_detail = Expenditure_Entry.objects.get(pk=expenditure_id)
        return expenditure_entry(request, expenditure_detail=expenditure_entry_detail)
    return render(request, 'index.html')


@csrf_protect
def delete_expense(request, expenditure_id):
    if request.user.is_authenticated:
        expenditure_entry_detail = Expenditure_Entry.objects.get(pk=expenditure_id)
        expenditure_entry_detail.delete()
        return expenditure_entry(request)
    return render(request, 'index.html')


def total_amount_expenditure_entry(request):
    if request.user.is_authenticated:
        return render(request, 'expenditure_total_iframe.html')
    return render(request, 'index.html')


@csrf_protect
def modify_arrival(request, arrival_id):
    if request.user.is_authenticated:
        arrival_entry_obj = Arrival_Entry.objects.get(pk=arrival_id)
        arrival_goods_objs = Arrival_Goods.objects.filter(arrival_entry=arrival_entry_obj).order_by('-id')

        today = arrival_entry_obj.date

        return render(request, 'modify_arrival_entry.html',
                      {'arrival_detail': arrival_entry_obj, 'arrival_goods_objs': arrival_goods_objs, 'NEW': False,
                       "today": today})
    return render(request, 'index.html')


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_arrival_goods_iteam_name(request):
    [...]
    iteam_name_list = {}
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    arrival_detail_object = Arrival_Goods.objects.filter(shop=shop_detail_object).filter(id=request.GET['selected_lot'])

    for arrival_entry in arrival_detail_object:
        iteam_name_list[arrival_entry.iteam_name] = arrival_entry.qty

    data = {'iteam_name_list': iteam_name_list}
    return Response(data, status=status.HTTP_200_OK)


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_arrival_goods_api(request):
    [...]
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    arrival_goods_obj = Arrival_Goods.objects.filter(shop=shop_detail_object, qty__gte=1)

    mylist = {}
    for iteam in arrival_goods_obj:
        mylist[iteam.id] = iteam.qty

    return JsonResponse(mylist, status=status.HTTP_200_OK)


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_arrival_duplicate_validation_api(request):
    [...]
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    respones = Arrival_Entry.objects.filter(shop=shop_detail_object).filter(lorry_no=request.GET['lorry_no']).filter(
        date=request.GET['date'])

    if respones.count() <= 0:
        return JsonResponse(data={'NOT_FOUND': True}, status=status.HTTP_200_OK)
    else:
        return JsonResponse(data={'NOT_FOUND': False}, status=status.HTTP_404_NOT_FOUND)


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_arrival_goods_list(request):
    [...]
    iteam_goods_list = {}
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    arrival_detail_object = Arrival_Goods.objects.filter(shop=shop_detail_object, qty__gte=1)

    for arrival_entry in arrival_detail_object:
        iteam_goods_list[arrival_entry.id] = arrival_entry.remarks

    data = {'iteam_goods_list': iteam_goods_list}
    return Response(data, status=status.HTTP_200_OK)


@csrf_protect
def add_arrival(request):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

        if len(request.POST['arrival_id']) <= 0:
            arrival_Entry_Obj = Arrival_Entry(
                gp_no=request.POST['gp_number'],
                date=getDate_from_string(request.POST['arrival_entry_date']),
                patti_name=request.POST['patti_name'],
                total_bags=request.POST['total_number_of_bags'],
                lorry_no=request.POST['lorry_number'],
                shop=shop_detail_object,
                Empty_data=False)
        else:
            arrival_Entry_Obj = Arrival_Entry.objects.get(id=request.POST['arrival_id'])  # object to update
            arrival_Entry_Obj.gp_no = request.POST['gp_number']
            arrival_Entry_Obj.date = getDate_from_string(request.POST['arrival_entry_date'])
            arrival_Entry_Obj.patti_name = request.POST['patti_name']
            arrival_Entry_Obj.total_bags = request.POST['total_number_of_bags']
            arrival_Entry_Obj.lorry_no = request.POST['lorry_number']
            arrival_Entry_Obj.shop = shop_detail_object
            arrival_Entry_Obj.Empty_data = False

        arrival_Entry_Obj.save()
        print(f"New arrival entry  = {arrival_Entry_Obj.id}")

        add_arrival_goods_iteam(request, list(request.POST), arrival_Entry_Obj, shop_detail_object)

        return home(request)

    return render(request, 'index.html')


def add_arrival_goods_iteam(request, request_list, arrival, shop_obj):
    if request.user.is_authenticated:
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
                arrival_Goods_obj = Arrival_Goods.objects.get(id=int(local_id))
                arrival_Goods_obj.iteam_name = request.POST[iteam_name_list[i]]
                arrival_Goods_obj.former_name = request.POST[former_name_list[i]]
                arrival_Goods_obj.initial_qty = request.POST[qty_list[i]]
                arrival_Goods_obj.qty = request.POST[qty_list[i]]
                arrival_Goods_obj.advance = request.POST[advance_amount_list[i]]
                arrival_Goods_obj.weight = request.POST[weight_list[i]]
                arrival_Goods_obj.remarks = request.POST[remarks_list[i]]

                arrival_Goods_obj.save()
                print(f"Update Arrival Goods Iteam  = {arrival_Goods_obj.id}")

            else:

                arrival_Goods_obj = Arrival_Goods(
                    iteam_name=request.POST[iteam_name_list[i]],
                    shop=shop_obj,
                    arrival_entry=arrival,
                    former_name=request.POST[former_name_list[i]],
                    advance=request.POST[advance_amount_list[i]],
                    initial_qty=request.POST[qty_list[i]],
                    qty=request.POST[qty_list[i]],
                    weight=request.POST[weight_list[i]],
                    remarks=request.POST[remarks_list[i]],
                )

                arrival_Goods_obj.save()
                print(f"New Arrival Goods Iteam  = {arrival_Goods_obj.id}")
    return render(request, 'index.html')


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_lorry_number_for_date(request, lorry_date):
    [...]
    lorry_number_list = []
    lorry_date = getDate_from_string(lorry_date)
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

    arrival_detail_object = Arrival_Entry.objects.filter(shop=shop_detail_object)
    for arrival_entry in arrival_detail_object:
        if arrival_entry.date == lorry_date and arrival_entry.Empty_data is False:
            lorry_number_list.append(arrival_entry.lorry_no)

    data = {'lorry_number_list': lorry_number_list}
    return Response(data, status=status.HTTP_200_OK)


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
        lorry_no=lorry_number,
        date=patti_date)

    arrival_good_object = Arrival_Goods.objects.filter(
        shop=shop_detail_object,
        arrival_entry=arrival_detail_object,
        patti_status=False
    )

    for arrival_goods_entry in arrival_good_object:
        farmer_name_list.append(arrival_goods_entry.former_name)

    data = {'farmer_list': farmer_name_list}
    return Response(data, status=status.HTTP_200_OK)


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_sales_list_for_arrival_iteam_list(request):
    [...]

    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

    lorry_number = request.GET['patti_lorry']
    patti_date = getDate_from_string(request.GET['patti_date'])
    patti_farmer = request.GET['patti_farmer']

    arrival_detail_object = Arrival_Entry.objects.get(
        shop=shop_detail_object,
        lorry_no=lorry_number,
        date=patti_date)

    arrival_good_object = Arrival_Goods.objects.filter(
        shop=shop_detail_object,
        arrival_entry=arrival_detail_object,
        former_name=patti_farmer,
        patti_status=False
    )

    advance = 0

    sales_array = []
    arrival_entry_with_no_sales = []
    for arrival_single_goods in arrival_good_object:
        print(arrival_single_goods.id)
        if float(arrival_single_goods.advance) > 0:
            advance = arrival_single_goods.advance

        sales_iteam_list = Sales_Bill_Iteam.objects.filter(
            arrival_goods=arrival_single_goods
        )
        if len(sales_iteam_list) <= 0:
            arrival_entry_with_no_sales.append(arrival_single_goods)
        else:
            for sales in sales_iteam_list:
                sales_array.append(sales)

    sales_response_list = []
    for single_sales in sales_array:
        sales_dict = {
            'iteam_name': single_sales.iteam_name,
            'net_weight': single_sales.net_weight,
            'sold_qty': single_sales.bags}

        arrival_good_object = Arrival_Goods.objects.get(
            id=single_sales.arrival_goods.id,
        )

        sales_dict['lot_number'] = arrival_good_object.remarks
        sales_dict['arrival_qty'] = arrival_good_object.qty
        sales_dict['rates'] = single_sales.rates
        sales_dict['amount'] = single_sales.amount

        sales_response_list.append(sales_dict)

    for single_arrival_entry in arrival_entry_with_no_sales:
        arrival_single_entry = {
            'iteam_name': single_arrival_entry.iteam_name,
            'net_weight': single_arrival_entry.weight,
            'sold_qty': 0,
            'lot_number': single_arrival_entry.remarks,
            'arrival_qty': single_arrival_entry.qty,
            'rates': 0,
            'amount': 0
        }
        sales_response_list.append(arrival_single_entry)

    sales_response_list = grouping_sales_bill_entry(sales_response_list)

    data = {
        'farmer_advance': advance,
        'sales_goods_list': sales_response_list
    }

    return Response(data, status=status.HTTP_200_OK)


def grouping_sales_bill_entry(sales_response_list: list):
    group_list = {}
    response = []
    for index, single_item in enumerate(sales_response_list):
        if single_item['lot_number'] not in group_list:
            group_list[single_item['lot_number']] = single_item
        else:
            temp_dict = group_list[single_item['lot_number']]
            temp_dict['sold_qty'] = float(temp_dict['sold_qty']) + float(single_item['sold_qty'])
            temp_dict['amount'] = float(temp_dict['amount']) + float(single_item['amount'])
            temp_dict['net_weight'] = float(temp_dict['net_weight']) + float(single_item['net_weight'])
            temp_dict['rates'] = (temp_dict['amount'] / temp_dict['net_weight']) * float(temp_dict['sold_qty'])
            group_list[single_item['lot_number']] = temp_dict

    for value in group_list.values():
        response.append(value)
    return response


def generate_patti_pdf_bill(request):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

        patti_entry_obj = Patti_entry.objects.get(id=request.POST['patti_bill_id'])
        patti_entry_obj.lorry_no = request.POST['patti_lorry_number']
        patti_entry_obj.shop = shop_detail_object
        patti_entry_obj.date = getDate_from_string(request.POST['patti_entry_date'])
        patti_entry_obj.advance = request.POST['advance_amount']
        patti_entry_obj.farmer_name = request.POST['patti_farmer_name']
        patti_entry_obj.total_weight = request.POST['total_weight']
        patti_entry_obj.hamali = request.POST['hamali']
        patti_entry_obj.net_amount = request.POST['net_amount']
        patti_entry_obj.Empty_data = False

        patti_entry_obj.save()
        print(f"New Patti entry Iteam  = {patti_entry_obj.id}")

        arrival_detail_object = Arrival_Entry.objects.get(
            shop=shop_detail_object,
            lorry_no=request.POST['patti_lorry_number'],
            date=getDate_from_string(request.POST['patti_entry_date']))

        arrival_good_object = Arrival_Goods.objects.get(
            shop=shop_detail_object,
            arrival_entry=arrival_detail_object,
            former_name=request.POST['patti_farmer_name'],

        )
        arrival_good_object.patti_status = True
        arrival_good_object.save()

        add_patti_iteam_list(request, list(request.POST), patti_entry_obj)
        generate_pdf(request)
        return patti_list(request)
    return render(request, 'index.html')


def add_patti_iteam_list(request, request_list, patti_entry_obj):
    if request.user.is_authenticated:
        iteam_name_list = []
        lot_number_list = []
        weight_list = []
        rate_list = []
        amount_list = []

        for i in request_list:
            iteam_name_list_regrex = re.search("^.*_iteam_name$", i)
            if iteam_name_list_regrex:
                iteam_name_list.append(i)

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

        for i in range(0, len(iteam_name_list)):
            patti_obj = Patti_entry_list(
                iteam=request.POST[iteam_name_list[i]],
                lot_no=request.POST[lot_number_list[i]],
                weight=request.POST[weight_list[i]],
                rate=request.POST[rate_list[i]],
                amount=request.POST[amount_list[i]],
                patti=patti_entry_obj
            )

            patti_obj.save()

    return render(request, 'index.html')


def generate_pdf(request):
    # Create a byte stream buffer
    buf = io.BytesIO()

    # Create a canvas
    c = canvas.Canvas(buf, pagesize=letter, bottomup=0)

    # Text object
    textOb = c.beginText()
    textOb.setTextOrigin(inch, inch)
    textOb.setFont("Helvetica", 14)

    # Add some lines of text
    lines = [
        "This is line 1",
        "This is line 2",
        "This is line 3"
    ]

    # loops
    for line in lines:
        textOb.textLine(line)

    c.drawText(textOb)
    c.showPage()
    c.save()

    buf.seek(0)

    # Return something
    return FileResponse(buf, as_attachment=True, filename="dummy.pdf")


@csrf_protect
def edit_sales_bill_entry(request, sales_id):
    if request.user.is_authenticated:
        sales_obj = Sales_Bill_Entry.objects.get(pk=sales_id)
        sales_iteam_objs = Sales_Bill_Iteam.objects.filter(Sales_Bill_Entry=sales_obj).order_by('-id')

        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        arrival_detail_object = Arrival_Goods.objects.filter(shop=shop_detail_object, qty__gte=1)

        return render(request, 'modify_sales_bill_entry.html',
                      {'sales_bill_detail': False,
                       "arrival_goods_detail": arrival_detail_object,
                       "sales_obj": sales_obj,
                       "sales_iteam_objs": sales_iteam_objs
                       }
                      )
    return render(request, 'index.html')


@csrf_protect
def edit_patti_entry(request, patti_id):
    if request.user.is_authenticated:
        patti_bill_detail = Patti_entry.objects.get(pk=patti_id)
        today = patti_bill_detail.date

        patti_entry_obj = Patti_entry_list.objects.filter(patti=patti_bill_detail)

        return render(request, 'modify_patti_entry.html',
                      {'patti_bill_detail': patti_bill_detail,
                       "today": today,
                       "patti_entry_obj": patti_entry_obj,
                       "NEW": False}
                      )
    return render(request, 'index.html')


@api_view(['GET'])
def get_authenticate_api(request):
    user = auth.authenticate(username=request.GET['username'], password=request.GET['password'])
    if user is not None:
        auth.login(request, user)
        shop_object = Shop.objects.get(shop_owner=user.id)

        data = {'u_id': user.id, 'shop_id': shop_object.id}
        return Response(data, status=status.HTTP_200_OK)
    else:
        data = {'error_message': "Invalid credentials"}
        return Response(data, status=status.HTTP_401_UNAUTHORIZED)


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


@api_view(['GET'])
def search_farmer_ledger(request):
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
    farmerLedgerObject = FarmerLedger.objects.filter(shop=shop_detail_object).filter(
        name__icontains=request.GET['search_text']) | CustomerLedger.objects.filter(shop=shop_detail_object).filter(
        contact__icontains=request.GET['search_text']) | CustomerLedger.objects.filter(shop=shop_detail_object).filter(
        place__icontains=request.GET['search_text'])
    response = []
    for farmer in farmerLedgerObject:
        farmer_dict = {
            'id': farmer.id,
            'name': farmer.name,
            'contact': farmer.contact,
            'place': farmer.place
        }
        response.append(farmer_dict)
    if len(response) >= 1:
        return JsonResponse(data={'FOUND': True, 'result': response}, status=status.HTTP_200_OK)
    else:
        return JsonResponse(data={'FOUND': False}, status=status.HTTP_404_NOT_FOUND)


@csrf_protect
def report(request):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        return render(request, 'report.html', {
            'shop_details': shop_detail_object,
        })
    return render(request, 'index.html')
