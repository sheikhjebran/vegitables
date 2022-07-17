from django.contrib import admin
from .models import Misc_Entry, Shop, Arrival_Entry, Arrival_Goods

# Register your models here.

admin.site.register(Shop)
admin.site.register(Arrival_Entry)
admin.site.register(Arrival_Goods)
admin.site.register(Misc_Entry)