from django.contrib import admin
from .models import (
    ExpenditureEntry,
    PattiEntry,
    PattiEntryList,
    SalesBillEntry,
    SalesBillItem,
    Shop,
    ArrivalEntry,
    ArrivalGoods,
    Index)

# Register your models here.

admin.site.register(Shop)
admin.site.register(ArrivalEntry)
admin.site.register(ArrivalGoods)
admin.site.register(ExpenditureEntry)
admin.site.register(SalesBillEntry)
admin.site.register(SalesBillItem)
admin.site.register(PattiEntry)
admin.site.register(PattiEntryList)
admin.site.register(Index)
