from django.contrib import admin
from .models import Misc_Entry, Sales_Bill_Entry, Sales_Bill_Iteam, Shop, Arrival_Entry, Arrival_Goods

# Register your models here.

admin.site.register(Shop)
admin.site.register(Arrival_Entry)
admin.site.register(Arrival_Goods)
admin.site.register(Misc_Entry)
admin.site.register(Sales_Bill_Entry)
admin.site.register(Sales_Bill_Iteam)