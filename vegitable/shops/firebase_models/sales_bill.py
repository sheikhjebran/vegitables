from django_firebase_orm import Manager, Model


class SalesBillEntryDocument(Model):
    shop_id = ''
    sales_bill_id = ''
    payment_type = ''
    customer_name = ''
    date = ''
    rmc = 0.0
    commission = 0.0
    cooli = 0.0
    total_amount = 0.0
    paid_amount = 0.0
    balance_amount = 0.0
    empty_data = False
    items = []
    created_at_ms = 0


SalesBillEntryDocument.objects = Manager(SalesBillEntryDocument)