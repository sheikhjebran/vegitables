from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages, auth

from .models import Shop, Arrival_Entry, Arrival_Goods
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
    return home(request,current_page=page_number+1)


def home_prev_page(request, page_number):
    if page_number > 1:
        return home(request,current_page=page_number-1)
    else:
        return home(request)

@csrf_protect
def home(request, page=10, current_page=1):
    if request.user.is_authenticated:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        try:
            arrival_entry_detail = Arrival_Entry.objects.filter(shop=shop_detail_object).order_by('-id')[:page * current_page]
        except Exception as error:
            print(error)
            arrival_entry_detail = None

        return render(request, 'home.html',
                      {
                          'shop_details': shop_detail_object,
                          'arrival_detail': arrival_entry_detail,
                          'current_page': current_page,

                      })
    else:
        return render(request, 'index.html')


def logout(request):
    auth.logout(request)
    return render(request, 'index.html')


def add_new_arrival_entry(request):
    return render(request, 'add_arrival_entry.html')


@csrf_protect
def add_arrival(request):
    shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

    arrival_Entry_Obj = Arrival_Entry(
        gp_no=request.POST['gp_number'],
        date=datetime.datetime.today(),
        patti_name=request.POST['patti_name'],
        total_bags=request.POST['total_number_of_bags'],
        advance=request.POST['advance_amount'],
        shop=shop_detail_object)

    arrival_Entry_Obj.save()

    print(f"New arrival entry  = {arrival_Entry_Obj.id}")

    newLIst = [list(request.POST)[i:i + 4] for i in range(5, len(list(request.POST)), 4)]

    for entry in newLIst:
        arrival_Goods_obj = Arrival_Goods(
            shop = shop_detail_object,
            arrival_entry = arrival_Entry_Obj,
            former_name = request.POST[list(entry)[0]],
            qty = request.POST[list(entry)[1]],
            weight = request.POST[list(entry)[2]],
            remarks = request.POST[list(entry)[3]],
        )
        arrival_Goods_obj.save()

    return home(request)


def getDate_from_string(stringDate):
    mystringDate = str(stringDate).split("-")
    return datetime.date(int(mystringDate[0]), int(mystringDate[1]), int(mystringDate[2]))

