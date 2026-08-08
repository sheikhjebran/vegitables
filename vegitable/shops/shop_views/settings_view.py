from django.http import JsonResponse
from django.shortcuts import render

from ..repositories.shop_metadata_repository import ShopMetadataRepository


shop_metadata_repository = ShopMetadataRepository()


def _load_shop_metadata(user_id):
    return shop_metadata_repository.require_by_owner_user_id(user_id)


def navigate_to_settings(request):
    if request.user.is_authenticated:
        try:
            index_instance = _load_shop_metadata(request.user.id)
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)
        return render(request, 'Settings/settings.html', {'index_data': index_instance, })
    return render(request, 'index.html')


def update_prefix(request):
    if request.user.is_authenticated:
        arrival_entry_prefix = request.POST['arrival_entry_prefix']
        sales_bill_entry_prefix = request.POST['sales_entry_prefix']
        patti_entry_prefix = request.POST['patti_entry_prefix']
        expenditure_entry_prefix = request.POST['expenditure_entry_prefix']
        credit_bill_entry_prefix = request.POST['credit_entry_prefix']
        shilk_entry_prefix = request.POST['shilk_entry_prefix']
        customer_ledger_prefix = request.POST['customer_ledger_prefix']
        farmer_ledger_prefix = request.POST['farmer_ledger_prefix']
        inventory_prefix = request.POST['inventory_prefix']

        try:
            index_instance = shop_metadata_repository.update_prefixes(
                request.user.id,
                arrival_entry_prefix=arrival_entry_prefix,
                sales_bill_entry_prefix=sales_bill_entry_prefix,
                patti_entry_prefix=patti_entry_prefix,
                expenditure_entry_prefix=expenditure_entry_prefix,
                credit_bill_entry_prefix=credit_bill_entry_prefix,
                shilk_entry_prefix=shilk_entry_prefix,
                customer_ledger_prefix=customer_ledger_prefix,
                farmer_ledger_prefix=farmer_ledger_prefix,
                inventory_prefix=inventory_prefix,
            )
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)
        return render(request, 'Settings/settings.html', {'index_data': index_instance, })

    return render(request, 'index.html')
