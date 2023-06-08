from datetime import date, timedelta, timezone
from email.policy import default
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


class Misc_Entry(models.Model):
    date = DateField()
    expense_type = CharField(max_length=50)
    amount = FloatField(max_length=100)
    remark = CharField(max_length=255)
    shop = ForeignKey(Shop, on_delete=models.CASCADE)
    Empty_data = BooleanField(default=True)

    def __str__(self):
        return f"{self.id}-{self.expense_type}-{self.amount}-{self.remark}"


class Arrival_Entry(models.Model):
    gp_no = CharField(max_length=100)
    lorry_no = CharField(max_length=100, default='')
    date = DateField()
    patti_name = CharField(max_length=50)
    total_bags = IntegerField()
    shop = ForeignKey(Shop, on_delete=models.CASCADE)
    Empty_data = BooleanField(default=True)

    def __str__(self):
        return f"{self.id} - {self.gp_no} - {self.date} - {self.total_bags}- {self.lorry_no}"


class Arrival_Goods(models.Model):
    shop = ForeignKey(Shop, on_delete=models.CASCADE)
    arrival_entry = ForeignKey(Arrival_Entry, on_delete=models.CASCADE)
    former_name = CharField(max_length=50)
    qty = IntegerField()
    weight = FloatField(max_length=100)
    remarks = CharField(max_length=50)
    iteam_name = CharField(max_length=100)
    advance = FloatField(max_length=100, default=0)
    patti_status = BooleanField(default=False)

    def __str__(self):
        return f"{self.id} - {self.shop} -{self.former_name}"


class Sales_Bill_Entry(models.Model):
    payment_type = CharField(max_length=10)
    customer_name = CharField(max_length=50)
    date = DateField()
    shop = ForeignKey(Shop, on_delete=models.CASCADE)
    rmc = FloatField(max_length=50)
    commission = FloatField(max_length=50)
    cooli = FloatField(max_length=50)
    total_amount = FloatField(max_length=50)
    Empty_data = BooleanField(default=True)

    def __str__(self):
        return f"{self.id}-{self.customer_name}-{self.total_amount}"


class Sales_Bill_Iteam(models.Model):
    iteam_name = CharField(max_length=10)
    arrival_goods = ForeignKey(Arrival_Goods, on_delete=models.CASCADE)
    bags = CharField(max_length=50)
    net_weight = FloatField(max_length=50)
    rates = FloatField(max_length=50)
    amount = FloatField(max_length=50)
    Sales_Bill_Entry = ForeignKey(Sales_Bill_Entry, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id}-{self.iteam_name}-{self.bags}-{self.net_weight}-{self.amount}"


class Patti_entry(models.Model):
    lorry_no = CharField(max_length=100)
    date = DateField()
    advance = FloatField(max_length=100)
    farmer_name = CharField(max_length=100)
    total_weight = FloatField(max_length=100)
    hamali = FloatField(max_length=100)
    net_amount = FloatField(max_length=100)
    shop = ForeignKey(Shop, on_delete=models.CASCADE)
    Empty_data = BooleanField(default=True)

    def __str__(self):
        return f"{self.lorry_no}- {self.farmer_name} - {self.total_weight} - {self.net_amount} -{self.shop}"


class Patti_entry_list(models.Model):
    iteam = CharField(max_length=100)
    lot_no = CharField(max_length=100)
    weight = CharField(max_length=100)
    rate = CharField(max_length=100)
    amount = FloatField(max_length=100)
    patti = ForeignKey(Patti_entry, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.iteam}- {self.lot_no}- {self.weight}- {self.amount} - {self.patti}"


class CustomerLedger(models.Model):
    name = CharField(max_length=100)
    contact = CharField(max_length=100)
    address = CharField(max_length=400)
    shop = ForeignKey(Shop, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id}-{self.name}-{self.contact}-{self.address}"


class FarmerLedger(models.Model):
    name = CharField(max_length=100)
    contact = CharField(max_length=100)
    place = CharField(max_length=400)
    shop = ForeignKey(Shop, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id}-{self.name}-{self.contact}-{self.place}"
