from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.db.models import CharField, IntegerField, ForeignKey, DateField, BooleanField, \
    FloatField


class Shop(models.Model):
    shop_name = CharField(max_length=50)
    shop_location = CharField(max_length=255)
    shop_address = CharField(max_length=255)
    shop_owner = ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return '%s %s' % (self.shop_owner, self.shop_name)


class Index(models.Model):
    expenditure_entry_prefix = CharField(max_length=50)
    expenditure_entry_counter = IntegerField()
    arrival_entry_prefix = CharField(max_length=50)
    arrival_entry_counter = IntegerField()
    sales_bill_entry_prefix = CharField(max_length=50)
    sales_bill_entry_counter = IntegerField()
    patti_entry_prefix = CharField(max_length=50)
    patti_entry_counter = IntegerField()
    customer_ledger_prefix = CharField(max_length=50)
    customer_ledger_counter = IntegerField()
    farmer_ledger_prefix = CharField(max_length=50)
    farmer_ledger_counter = IntegerField()
    credit_bill_entry_prefix = CharField(max_length=50)
    credit_bill_entry_counter = IntegerField()
    shilk_entry_prefix = CharField(max_length=50)
    shilk_entry_counter = IntegerField()
    inventory_prefix = CharField(max_length=50)
    inventory_counter = IntegerField()
    shop = ForeignKey(Shop, on_delete=models.CASCADE)

    def __str__(self):
        return '%s' % (self.shop)


class ExpenditureEntry(models.Model):
    date = DateField()
    expense_type = CharField(max_length=50)
    amount = FloatField(max_length=100)
    remark = CharField(max_length=255)
    shop = ForeignKey(Shop, on_delete=models.CASCADE)
    Empty_data = BooleanField(default=True)

    def __str__(self):
        return f"{self.id}-{self.expense_type}-{self.amount}-{self.remark}"


class ArrivalEntry(models.Model):
    gp_no = CharField(max_length=100)
    lorry_no = CharField(max_length=100, default='')
    date = DateField()
    patti_name = CharField(max_length=50)
    total_bags = IntegerField()
    shop = ForeignKey(Shop, on_delete=models.CASCADE)
    Empty_data = BooleanField(default=True)
    arrival_id = CharField(max_length=100)  # Added the ArrivalId field

    def __str__(self):
        return f"{self.id} - {self.arrival_id}- {self.gp_no} - {self.date} - {self.total_bags}- {self.lorry_no}"


class ArrivalGoods(models.Model):
    shop = ForeignKey(Shop, on_delete=models.CASCADE)
    arrival_entry = ForeignKey(ArrivalEntry, on_delete=models.CASCADE)
    former_name = CharField(max_length=50)
    initial_qty = IntegerField()
    qty = IntegerField()
    weight = FloatField(max_length=100)
    remarks = CharField(max_length=50)
    item_name = CharField(max_length=100)
    advance = FloatField(max_length=100, default=0)
    patti_status = BooleanField(default=False)

    def __str__(self):
        return f"{self.id} - {self.shop} -{self.former_name}"


class SalesBillEntry(models.Model):
    payment_type = CharField(max_length=10)
    customer_name = CharField(max_length=50)
    date = DateField()
    shop = ForeignKey(Shop, on_delete=models.CASCADE)
    rmc = FloatField(max_length=50)
    commission = FloatField(max_length=50)
    cooli = FloatField(max_length=50)
    total_amount = FloatField(max_length=50)
    paid_amount = FloatField(max_length=50)
    balance_amount = FloatField(max_length=50)
    Empty_data = BooleanField(default=True)
    sales_bill_id = CharField(max_length=100)  # Added SalesBill ID field

    def __str__(self):
        return f"{self.id}-{self.customer_name}-{self.total_amount}"


class SalesBillItem(models.Model):
    item_name = CharField(max_length=10)
    arrival_goods = ForeignKey(ArrivalGoods, on_delete=models.CASCADE)
    bags = CharField(max_length=50)
    net_weight = FloatField(max_length=50)
    rates = FloatField(max_length=50)
    amount = FloatField(max_length=50)
    Sales_Bill_Entry = ForeignKey(SalesBillEntry, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id}-{self.item_name}-{self.bags}-{self.net_weight}-{self.amount}"


class PattiEntry(models.Model):
    lorry_no = CharField(max_length=100)
    date = DateField()
    advance = FloatField(max_length=100)
    farmer_name = CharField(max_length=100)
    total_weight = FloatField(max_length=100)
    hamali = FloatField(max_length=100)
    net_amount = FloatField(max_length=100)
    patti_id = CharField(max_length=100)
    shop = ForeignKey(Shop, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.lorry_no}- {self.farmer_name} - {self.total_weight} - {self.net_amount} -{self.shop}"


class PattiEntryList(models.Model):
    item = CharField(max_length=100)
    lot_no = CharField(max_length=100)
    weight = CharField(max_length=100)
    rate = CharField(max_length=100)
    amount = FloatField(max_length=100)
    patti = ForeignKey(PattiEntry, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.item}- {self.lot_no}- {self.weight}- {self.amount} - {self.patti}"


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


class CreditBillEntry(models.Model):
    customer_name = CharField(max_length=100)
    sales_bill = ForeignKey(SalesBillEntry, on_delete=models.CASCADE)
    shop = ForeignKey(Shop, on_delete=models.CASCADE)
    initial_credit_bill_amount = FloatField(max_length=100)
    def __str__(self):
        return f"{self.id}-{self.customer_name}"


class CreditBillHistory(models.Model):
    date = DateField()
    amount = FloatField(max_length=100)
    payment_mode = CharField(max_length=100)
    credit_bill = ForeignKey(CreditBillEntry, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.id}-{self.date}-{self.amount}-{self.credit_bill}"

class MobileSalesBill(models.Model):
    shop = ForeignKey(Shop, on_delete=models.CASCADE)
    name = CharField(max_length=100)
    lot_no = CharField(max_length=100)
    total_bags = IntegerField()
    net_weight = FloatField(max_length=100)

    def __str__(self):
        return f"{self.id}-{self.name}-{self.lot_no}-{self.net_weight}-{self.shop}"
