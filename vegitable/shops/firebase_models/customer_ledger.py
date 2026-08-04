from django_firebase_orm import Manager, Model


class CustomerLedgerDocument(Model):
    shop_id = ''
    name = ''
    contact = ''
    address = ''
    name_lower = ''
    contact_normalized = ''
    address_lower = ''
    created_at_ms = 0


CustomerLedgerDocument.objects = Manager(CustomerLedgerDocument)