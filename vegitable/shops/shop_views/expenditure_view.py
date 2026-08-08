import datetime

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_protect

from .. import utility
from ..repositories.expenditure_repository import ExpenditureRepository
from ..repositories.shop_metadata_repository import ShopMetadataRepository


expenditure_repository = ExpenditureRepository()
shop_metadata_repository = ShopMetadataRepository()


def _expenditure_firebase_required_message():
    return 'Enable USE_FIREBASE_EXPENDITURE=True. SQL expenditure path has been removed.'


def _load_shop_metadata(user_id):
    return shop_metadata_repository.require_by_owner_user_id(user_id)


def expenditure_entry(request, current_page=1, expenditure_detail=None):
    total_amount = 0
    expenditure_events_today = []
    if request.user.is_authenticated:
        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)

        if not expenditure_repository.using_firebase():
            return JsonResponse({'error': _expenditure_firebase_required_message()}, status=400)

        try:
            today = datetime.date.today().isoformat()
            expenditure_events_today = expenditure_repository.list_by_shop_and_date(
                shop_detail_object.pk,
                today,
            )

            total_amount = sum(float(entry.amount) for entry in expenditure_events_today)

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


@csrf_protect
def add_expenditure_entry(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            if request.POST.get('form_token') == str(request.session.get('form_token')):
                # Remove the token from the session
                del request.session['form_token']
                try:
                    shop_detail_object = _load_shop_metadata(request.user.id)
                except ValueError as error:
                    return JsonResponse({'error': str(error)}, status=400)
                if request.POST['expenditure_id'] == "None":

                    expenditure_repository.create(
                        shop_id=shop_detail_object.pk,
                        date=datetime.date.today(),
                        expense_type=str(request.POST['expense_type']).upper(),
                        amount=request.POST['expense_amount'],
                        remark=request.POST['expense_remark'],
                    )
                else:
                    expenditure_repository.update(
                        record_id=request.POST['expenditure_id'],
                        shop_id=shop_detail_object.pk,
                        date=datetime.date.today(),
                        expense_type=str(request.POST['expense_type']).upper(),
                        amount=request.POST['expense_amount'],
                        remark=request.POST['expense_remark'],
                    )
            request.session['form_token'] = utility.generate_unique_number()
            return expenditure_entry(request)

    return render(request, 'index.html')


@csrf_protect
def edit_expense(request, expenditure_id):
    if request.user.is_authenticated:
        if not expenditure_repository.using_firebase():
            return JsonResponse({'error': _expenditure_firebase_required_message()}, status=400)

        expenditure_entry_detail = expenditure_repository.get_by_id(expenditure_id)
        return expenditure_entry(request, expenditure_detail=expenditure_entry_detail)
    return render(request, 'index.html')


@csrf_protect
def delete_expense(request, expenditure_id):
    if request.user.is_authenticated:
        if not expenditure_repository.using_firebase():
            return JsonResponse({'error': _expenditure_firebase_required_message()}, status=400)

        expenditure_repository.delete(expenditure_id)
        return expenditure_entry(request)
    return render(request, 'index.html')


def expenditure_next_page(request, page_number):
    return expenditure_entry(request, current_page=page_number + 1)


def expenditure_prev_page(request, page_number):
    if page_number > 1:
        return expenditure_entry(request, current_page=page_number - 1)
    else:
        return expenditure_entry(request)


def fetch_expenditures(request):
    search_date = request.GET.get('search_date')

    if search_date and request.user.is_authenticated:
        try:
            shop_detail_object = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)

        if not expenditure_repository.using_firebase():
            return JsonResponse({'error': _expenditure_firebase_required_message()}, status=400)

        expenditures = expenditure_repository.list_by_shop_and_date(
            shop_detail_object.pk,
            search_date,
        )

        # Prepare the result data to send back
        result_data = []
        for entry in expenditures:
            result_data.append({
                'id': entry.id,
                'expense_type': entry.expense_type,
                'amount': entry.amount,
                'remark': entry.remark,
                'date': entry.date
            })

        return JsonResponse(result_data, safe=False)  # Return as JSON
    else:
        # Return an empty list if no date is selected
        return JsonResponse([], safe=False)
