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
    qty = FloatField(max_length=100)
    weight = FloatField(max_length=100)
    remarks = CharField(max_length=50)

    def __str__(self):
        return f"{self.id} - {self.shop} -{self.former_name}"
