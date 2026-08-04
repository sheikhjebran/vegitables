from django_firebase_orm import Manager, Model


class MobileSalesBillDocument(Model):
    shop_id = ''
    name = ''
    lot_no = ''
    total_bags = 0
    net_weight = 0.0


MobileSalesBillDocument.objects = Manager(MobileSalesBillDocument)