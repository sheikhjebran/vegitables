from django_firebase_orm import Manager, Model


class ShopMetadataDocument(Model):
    owner_user_id = ''
    shop_id = 0
    shop_name = ''
    shop_location = ''
    shop_address = ''
    expenditure_entry_prefix = ''
    expenditure_entry_counter = 0
    arrival_entry_prefix = ''
    arrival_entry_counter = 0
    sales_bill_entry_prefix = ''
    sales_bill_entry_counter = 0
    patti_entry_prefix = ''
    patti_entry_counter = 0
    customer_ledger_prefix = ''
    customer_ledger_counter = 0
    farmer_ledger_prefix = ''
    farmer_ledger_counter = 0
    credit_bill_entry_prefix = ''
    credit_bill_entry_counter = 0
    shilk_entry_prefix = ''
    shilk_entry_counter = 0
    inventory_prefix = ''
    inventory_counter = 0
    created_at_ms = 0


ShopMetadataDocument.objects = Manager(ShopMetadataDocument)