from django_firebase_orm import Manager, Model


class ArrivalEntryDocument(Model):
    shop_id = ''
    arrival_id = ''
    gp_no = ''
    lorry_no = ''
    date = ''
    patti_name = ''
    total_bags = 0
    empty_data = False
    goods = []
    created_at_ms = 0


ArrivalEntryDocument.objects = Manager(ArrivalEntryDocument)