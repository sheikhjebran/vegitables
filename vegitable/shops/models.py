from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.db.models import CharField, IntegerField, FileField, ForeignKey, TextField, DateField, BooleanField, \
    EmailField, FloatField


class Shop(models.Model):
    shop_name = CharField(max_length=50)
    shop_location = CharField(max_length=255)
    shop_address = CharField(max_length=255)
    shop_owner = ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return '%s %s' % (self.shop_owner, self.shop_name)

class Sales_Bill_Entry(models.Model):
    payment_type = CharField(max_length=10)
    customer_name = CharField(max_length=50)
    date = DateField()
    shop = ForeignKey(Shop, on_delete=models.CASCADE)
    rmc = FloatField(max_length=50)
    commission = FloatField(max_length=50)
    cooli = FloatField(max_length=50)
    total_amount = FloatField(max_length=50)
    
    def __str__(self):
        return f"{self.id}-{self.customer_name}-{self.total_amount}"
    
class Sales_Bill_Iteam(models.Model):
    iteam_name = CharField(max_length=10)
    lot_number = CharField(max_length=50)
    bags = CharField(max_length=50)
    net_weight = FloatField(max_length=50)
    rates = FloatField(max_length=50)
    amount = FloatField(max_length=50)
    Sales_Bill_Entry = ForeignKey(Sales_Bill_Entry, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.id}-{self.lot_number}-{self.iteam_name}-{self.bags}-{self.net_weight}-{self.amount}"
    
class Misc_Entry(models.Model):
    date = DateField()
    expense_type = CharField(max_length=50)
    amount = FloatField(max_length=100)
    remark = CharField(max_length=255)
    shop = ForeignKey(Shop, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id}-{self.expense_type}-{self.amount}-{self.remark}"


class Arrival_Entry(models.Model):
    gp_no = CharField(max_length=100)
    date = DateField()
    patti_name = CharField(max_length=50)
    total_bags = IntegerField()
    advance = FloatField(max_length=100)    
    shop = ForeignKey(Shop, on_delete=models.CASCADE)
    

    def __str__(self):
        return f"{self.id} - {self.gp_no} - {self.date} - {self.total_bags}- {self.advance}"


class Arrival_Goods(models.Model):
    shop = ForeignKey(Shop, on_delete=models.CASCADE)
    arrival_entry = ForeignKey(Arrival_Entry, on_delete=models.CASCADE)
    former_name = CharField(max_length=50)
    qty = CharField(max_length=100)
    weight = FloatField(max_length=100)
    remarks = CharField(max_length=50)
    iteam_name = CharField(max_length=100)
    
    def __str__(self):
        return f"{self.id} - {self.shop} -{self.former_name}"
