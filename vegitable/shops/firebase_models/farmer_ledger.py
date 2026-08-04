from django_firebase_orm import Manager, Model


class FarmerLedgerDocument(Model):
    shop_id = ''
    name = ''
    contact = ''
    place = ''
    name_lower = ''
    contact_normalized = ''
    place_lower = ''
    created_at_ms = 0


FarmerLedgerDocument.objects = Manager(FarmerLedgerDocument)