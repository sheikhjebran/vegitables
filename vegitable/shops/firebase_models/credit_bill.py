from django_firebase_orm import Manager, Model


class CreditBillEntryDocument(Model):
    shop_id = ''
    customer_name = ''
    sales_bill_record_id = ''
    sales_bill_id = ''
    initial_credit_bill_amount = 0.0
    histories = []
    created_at_ms = 0


CreditBillEntryDocument.objects = Manager(CreditBillEntryDocument)
