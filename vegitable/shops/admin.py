from django.contrib import admin
from .models import Shop, Arrival_Entry, Arrival_Goods

# Register your models here.

admin.site.register(Shop)
admin.site.register(Arrival_Entry)
admin.site.register(Arrival_Goods)