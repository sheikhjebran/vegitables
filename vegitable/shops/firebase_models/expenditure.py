from django_firebase_orm import Manager, Model


class ExpenditureEntryDocument(Model):
    shop_id = ''
    date = ''
    expense_type = ''
    amount = 0.0
    remark = ''
    empty_data = False
    created_at_ms = 0


ExpenditureEntryDocument.objects = Manager(ExpenditureEntryDocument)
