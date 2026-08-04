from django_firebase_orm import Manager, Model


class PattiEntryDocument(Model):
    shop_id = ''
    patti_id = ''
    lorry_no = ''
    date = ''
    advance = 0.0
    farmer_name = ''
    total_weight = 0.0
    hamali = 0.0
    net_amount = 0.0
    items = []
    created_at_ms = 0


PattiEntryDocument.objects = Manager(PattiEntryDocument)
