from django.shortcuts import redirect, render, get_object_or_404

from ..models import Shop, Index


def navigate_to_settings(request):
    if request.user.is_authenticated:
        shop_instance = Shop.objects.get(shop_owner=request.user.id)
        index_instance = Index.objects.get(shop=shop_instance)
        return render(request, 'Settings/settings.html',{ 'index_data': index_instance,})
    return render(request, 'index.html')
