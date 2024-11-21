from django.shortcuts import redirect, render, get_object_or_404

from ..models import Shop, Index


def navigate_to_settings(request):
    if request.user.is_authenticated:
        shop_instance = Shop.objects.get(shop_owner=request.user.id)
        index_instance = Index.objects.get(shop=shop_instance)
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

        shop_instance = Shop.objects.get(shop_owner=request.user.id)
        index_instance = Index.objects.get(shop=shop_instance)

        index_instance.arrival_entry_prefix = arrival_entry_prefix
        index_instance.sales_bill_entry_prefix = sales_bill_entry_prefix
        index_instance.patti_entry_prefix = patti_entry_prefix
        index_instance.expenditure_entry_prefix = expenditure_entry_prefix
        index_instance.credit_bill_entry_prefix = credit_bill_entry_prefix
        index_instance.shilk_entry_prefix = shilk_entry_prefix
        index_instance.customer_ledger_prefix = customer_ledger_prefix
        index_instance.farmer_ledger_prefix = farmer_ledger_prefix
        index_instance.inventory_prefix = inventory_prefix

        index_instance.save()
        return render(request, 'Settings/settings.html', {'index_data': index_instance, })

    return render(request, 'index.html')
